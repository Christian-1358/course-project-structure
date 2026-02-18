import sqlite3
import os
import tornado.web

from app.handlers.base import BaseHandler


class PublicProfileHandler(BaseHandler):
    def get(self, user_id):
        try:
            uid = int(user_id)
        except ValueError:
            self.set_status(400)
            self.write("Usuário inválido")
            return

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(BASE_DIR, "usuarios.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("SELECT username, bio, photo FROM users WHERE id = ?", (uid,))
        row = c.fetchone()
        conn.close()

        if not row:
            self.set_status(404)
            self.write("Usuário não encontrado")
            return

        self.render(
            "public_profile.html",
            username=row["username"],
            bio=row["bio"] or "",
            photo=row["photo"] or "",
        )
