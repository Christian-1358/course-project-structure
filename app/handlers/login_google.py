import tornado.web
import tornado.auth
import sqlite3
import os

DB = os.path.abspath("usuarios.db")


class GoogleLoginHandler(tornado.web.RequestHandler,
                         tornado.auth.GoogleOAuth2Mixin):

    async def get(self):
        if not self.get_argument("code", False):
            await self.authorize_redirect(
        redirect_uri="http://milhaspro.home/auth/google",
          client_id=self.settings["google_oauth"]["key"],
                scope=["profile", "email"],
                response_type="code"
            )
            return

        user = await self.get_authenticated_user(
            redirect_uri="http://localhost:8080/auth/google",
            code=self.get_argument("code")
        )

        if not user:
            self.write("Erro ao autenticar com Google")
            return

        email = user["email"]
        nome = user.get("name", "GoogleUser")

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = c.fetchone()

        if row:
            user_id = row[0]
        else:
            c.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (nome, email, "google")
            )
            conn.commit()
            user_id = c.lastrowid

        conn.close()

        self.set_secure_cookie("user_id", str(user_id))

        self.redirect("/curso")
