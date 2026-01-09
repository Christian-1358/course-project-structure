import tornado.web
import sqlite3
import os

# Caminho do banco
DB = os.path.abspath("usuarios.db")


class EmailsLogadosHandler(tornado.web.RequestHandler):
    def get(self):
        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("""
            SELECT users.email
            FROM sessions
            JOIN users ON users.id = sessions.user_id
        """)

        emails = c.fetchall()
        conn.close()

        if not emails:
            self.write("Nenhum usuário logado.")
            return

        resposta = "E-MAILS LOGADOS:\n\n"
        for (email,) in emails:
            resposta += f"{email}\n"

        self.write(resposta)
