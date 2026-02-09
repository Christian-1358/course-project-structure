import tornado.web
import sqlite3
from app.handlers.base import BaseHandler
from app.utils.pagamento_utils import usuario_pagou

class CursoHandler(BaseHandler):

    def get_db_connection(self):
        import os
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
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

        # 🔒 Bloqueio se não pagou
        if not usuario_pagou(user_id):
            self.redirect("/pagamento")
            return

        conn = self.get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            conn.close()
            self.clear_all_cookies()
            self.redirect("/login")
            return

        notas = conn.execute("SELECT modulo, nota, data FROM provas_resultado WHERE user_id=? ORDER BY modulo ASC", (user_id,)).fetchall()
        conn.close()

        self.render("curso.html", usuario=user["nome"] or user["username"], user=user, notas=notas)
