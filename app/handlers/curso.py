import os
import sqlite3
import tornado.web
from app.handlers.base import BaseHandler


class CursoHandler(BaseHandler):

    def get_db_connection(self):
        BASE_DIR = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        conn = sqlite3.connect(os.path.join(BASE_DIR, "usuarios.db"))
        conn.row_factory = sqlite3.Row
        return conn

    @tornado.web.authenticated
    def get(self):
        user_id_cookie = self.get_secure_cookie("user_id")

        if not user_id_cookie:
            self.redirect("/login")
            return

        user_id = user_id_cookie.decode()

        conn = self.get_db_connection()

        # Dados do usuário
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not user:
            conn.close()
            self.clear_all_cookies()
            self.redirect("/login")
            return

        # Notas das provas
        notas = conn.execute("""
            SELECT modulo, nota, data
            FROM provas_resultado
            WHERE user_id = ?
            ORDER BY modulo ASC
        """, (user_id,)).fetchall()

        conn.close()

        self.render(
            "curso.html",
            usuario=user["nome"] if user["nome"] else user["username"],
            user=user,
            notas=notas
        )
