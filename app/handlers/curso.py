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

    # página agora aberta para qualquer pessoa; comentários requerem login
    def get(self):
        user_id = self.get_current_user()  # só retorna se logado e pagou

        conn = self.get_db_connection()
        user = None
        notas = []
        if user_id:
            user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            notas = conn.execute("SELECT modulo, nota, data FROM provas_resultado WHERE user_id=? ORDER BY modulo ASC", (user_id,)).fetchall()
        conn.close()

        self.render("curso.html", usuario=(user["nome"] or user["username"]) if user else "Visitante", user=user, notas=notas)
