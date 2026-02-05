import tornado.web
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.abspath(os.getcwd())
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

class ProvaFinalHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id")
        return int(user_id.decode()) if user_id else None

    @tornado.web.authenticated
    def get(self):
        user_id = self.current_user
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # Busca os resultados das provas
            c.execute("""
                SELECT modulo, MAX(nota) as maior_nota 
                FROM provas_resultado 
                WHERE user_id = ? 
                GROUP BY modulo
            """, (user_id,))
            
            rows = c.fetchall()
            resultados = {row['modulo']: row['maior_nota'] for row in rows}
            
            # Verificação de Módulos
            modulos_obrigatorios = [1, 2, 3, 4, 5]
            status_modulos = {m: resultados.get(m, 0) for m in modulos_obrigatorios}
            aprovado_em_todos = all(nota >= 6 for nota in status_modulos.values())

            # Log profissional no terminal para ajudar você a debugar
            print(f"--- Verificação de Acesso (User ID: {user_id}) ---")
            for m, nota in status_modulos.items():
                print(f"Módulo {m}: Nota {nota}")
            print(f"Aprovado: {'SIM' if aprovado_em_todos else 'NÃO'}")
            print("-----------------------------------------------")

            if aprovado_em_todos:
                self.render("prova_final.html", resultados=resultados)
            else:
                msg = "Você precisa de nota mínima 6.0 em todos os módulos!"
                self.write(f"<script>alert('{msg}'); window.location='/curso';</script>")

    @tornado.web.authenticated
    def post(self):
        try:
            nota_final = float(self.get_argument("nota_final", 0))
            user_id = self.current_user

            if nota_final >= 7.0:
                with sqlite3.connect(DB_PATH) as conn:
                    c = conn.cursor()
                    # Garante que a coluna certificado_fin existe ou atualiza o status
                    c.execute("UPDATE users SET certificado_fin = 1 WHERE id = ?", (user_id,))
                    conn.commit()
                self.redirect("/certificado/final?download=true")
            else:
                self.write("<script>alert('Nota insuficiente na Prova Final!'); window.location='/prova_final';</script>")
        except Exception as e:
            print(f"Erro ao processar prova final: {e}")
            self.write("Erro interno no servidor.")