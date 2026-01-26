import tornado.web
import sqlite3
from datetime import datetime

DB = "usuarios.db"


def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


class ProvaHandler(tornado.web.RequestHandler):
    def get(self, modulo):
        self.render("prova.html", modulo=modulo)

    def post(self, modulo):
        user_id = self.get_secure_cookie("user_id")

        if not user_id:
            self.redirect("/login")
            return

        gabarito = {
            1: "b", 2: "b", 3: "c", 4: "a", 5: "b",
            6: "d", 7: "a", 8: "c", 9: "a", 10: "d"
        }

        nota = 0

        for i in range(1, 11):
            r = self.get_body_argument(f"q{i}", None)
            if r == gabarito[i]:
                nota += 1

        media = nota

        conn = conectar()
        c = conn.cursor()

        if media >= 7:
            fim = datetime.now().strftime("%d/%m/%Y")

            c.execute("""
                UPDATE users
                SET fim_modulo1 = ?
                WHERE id = ?
            """, (fim, int(user_id)))

            conn.commit()
            conn.close()

            self.redirect("/certificado")
        else:
            conn.close()
            self.redirect(f"/recuperacao/{modulo}")
