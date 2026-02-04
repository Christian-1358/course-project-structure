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
            
            # Busca os resultados de todas as provas do usuário
            c.execute("""
                SELECT modulo, MAX(nota) as maior_nota 
                FROM provas_resultado 
                WHERE user_id = ? 
                GROUP BY modulo
            """, (user_id,))
            
            resultados = {row['modulo']: row['maior_nota'] for row in c.fetchall()}
            
            # Verificação Profissional: Todos os 5 módulos precisam de nota >= 6
            modulos_obrigatorios = [1, 2, 3, 4, 5]
            aprovado_em_todos = all(resultados.get(m, 0) >= 6 for m in modulos_obrigatorios)

            if aprovado_em_todos:
                # Libera a página da prova final
                self.render("prova_final.html", resultados=resultados)
            else:
                # Caso não tenha média, redireciona com mensagem de erro
                self.write("<script>alert('Você precisa de nota mínima 6.0 em todos os módulos para liberar a Prova Final!'); window.location='/dashboard';</script>")

    @tornado.web.authenticated
    def post(self):
        # Lógica para processar o envio da prova final
        nota_final = float(self.get_argument("nota_final", 0))
        user_id = self.current_user

        if nota_final >= 7.0: # Critério mais rigoroso para o certificado final
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("UPDATE users SET certificado_fin = 1 WHERE id = ?", (user_id,))
                conn.commit()
            self.redirect("/certificado/final?download=true")
        else:
            self.write("<script>alert('Nota insuficiente na Prova Final. Estude mais e tente novamente!'); window.location='/prova/final';</script>")