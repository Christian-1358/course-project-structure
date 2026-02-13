import tornado.web
import sqlite3
import os
from datetime import datetime
from app.utils.security import set_flow_allowed_if_referer, consume_flow_allowed, verify_flow_and_payment
from app.utils.admin_tools import conectar
from app.utils.pagamento_utils import usuario_pagou

class ProvaFinalHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id")
        return int(user_id.decode()) if user_id else None

    @tornado.web.authenticated
    def get(self):
        user_id = self.current_user
        # 1) Autenticado já garantido pelo decorator
        # 2) Primeiro checa se o usuário já tem direito direto (nota_final/certificado ou notas >=6 em todos os módulos)
        allow_bypass = False
        try:
            conn_check = conectar(); cur_check = conn_check.cursor()
            try:
                cur_check.execute("SELECT nota_final, certificado_fin FROM users WHERE id = ?", (user_id,))
                urow = cur_check.fetchone()
                if urow and ( (urow.get('certificado_fin') == 1) or (urow.get('nota_final') is not None and urow['nota_final'] != None and int(urow['nota_final']) >= 6) ):
                    allow_bypass = True
                else:
                    cur_check.execute("SELECT modulo, MAX(nota) as maior_nota FROM provas_resultado WHERE user_id = ? GROUP BY modulo", (user_id,))
                    rows_check = cur_check.fetchall()
                    resultados_check = {r['modulo']: r['maior_nota'] for r in rows_check}
                    required = [1,2,3,4,5]
                    allow_bypass = all(resultados_check.get(m, 0) >= 6 for m in required)
            finally:
                try: conn_check.close()
                except: pass
        except Exception as e:
            print(f"Erro ao checar bypass de provas: {e}")
            allow_bypass = False

        if allow_bypass:
            # usuário tem todas as notas necessárias — libera sem exigir pagamento/fluxo
            try:
                print(f"Prova final: bypass permitido para user {user_id}")
            except Exception:
                pass
        else:
            # 3) Verifica pagamento — somente se não houver bypass
            try:
                if not usuario_pagou(user_id):
                    self.set_status(403)
                    self.write('<h1>Acesso Negado (403)</h1><p>Pagamento pendente.</p>')
                    return
            except Exception as e:
                print(f"erro checando pagamento em prova final: {e}")
                self.set_status(500); self.write("Erro interno ao checar pagamento."); return

            # exige fluxo normal (referer ou cookie)
            if not verify_flow_and_payment(self, 'prova', 'final'):
                try:
                    print(f"verify_flow_and_payment denied access for user {user_id} to final prova")
                except Exception:
                    pass
                return

        conn = conectar()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Busca os resultados das provas dos módulos
        c.execute("""
            SELECT modulo, MAX(nota) as maior_nota 
            FROM provas_resultado 
            WHERE user_id = ? 
            GROUP BY modulo
        """, (user_id,))

        rows = c.fetchall()
        resultados = {row['modulo']: row['maior_nota'] for row in rows}

        # Verificação de Módulos (1 a 5)
        modulos_obrigatorios = [1, 2, 3, 4, 5]
        status_modulos = {m: resultados.get(m, 0) for m in modulos_obrigatorios}
        aprovado_em_todos = all(nota >= 6 for nota in status_modulos.values())

        try:
            print(f"Prova final check for user {user_id}: {status_modulos} aprovado={aprovado_em_todos}")
        except Exception:
            pass

        if aprovado_em_todos:
            self.render("prova_final.html", resultados=resultados)
        else:
            msg = "Você precisa de nota mínima 6.0 em todos os módulos para liberar a prova final!"
            self.write(f"<script>alert('{msg}'); window.location='/curso';</script>")

    @tornado.web.authenticated
    def post(self):
        try:
            # aceita acertos+total do front-end ou nota_final direto
            user_id = self.current_user
            acertos_arg = self.get_argument('acertos', None)
            total_arg = self.get_argument('total', None)

            if acertos_arg is not None and total_arg is not None:
                acertos = float(acertos_arg)
                total = float(total_arg)
                nota10 = (acertos / total) * 10.0 if total > 0 else 0.0
            else:
                nota10 = float(self.get_argument("nota_final", 0))

            # grava no banco: provas_resultado (modulo 6) com nota em escala do total (ex: acertos)
            conn = conectar(); c = conn.cursor()
            from datetime import datetime as _dt
            ts = _dt.now().strftime('%Y-%m-%d %H:%M:%S')

            # se vier acertos, registra nota raw (0..total) em provas_resultado
            if acertos_arg is not None and total_arg is not None:
                # remover entradas antigas do modulo 6 e inserir nova
                c.execute("DELETE FROM provas_resultado WHERE user_id = ? AND modulo = ?", (user_id, 6))
                c.execute("INSERT INTO provas_resultado (user_id, modulo, nota, aprovado, data) VALUES (?, ?, ?, ?, ?)", (user_id, 6, acertos, 1, ts))

            # atualiza users.nota_final em escala 0-10 quando possível
            try:
                c.execute("UPDATE users SET nota_final = ? WHERE id = ?", (round(nota10, 2), user_id))
            except Exception:
                pass

            # se nota >= 7.0 (70%) marca certificado_fin
            if nota10 >= 7.0:
                try:
                    c.execute("UPDATE users SET certificado_fin = 1 WHERE id = ?", (user_id,))
                except Exception:
                    pass

            conn.commit(); conn.close()

            if nota10 >= 7.0:
                self.redirect("/certificado/6")
            else:
                self.write("<script>alert('Nota insuficiente na Prova Final!'); window.location='/prova_final';</script>")
        except Exception as e:
            print(f"Erro ao processar prova final: {e}")
            self.write("Erro interno no servidor.")