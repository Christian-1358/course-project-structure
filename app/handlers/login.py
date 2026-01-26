from datetime import datetime
import tornado.web
import tornado.auth
import sqlite3
import hashlib
import uuid
import os

# ===============================
# CONFIG DB
# ===============================
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DB = os.path.join(BASE_DIR, "usuarios.db")


def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def hash_senha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ===============================
# LOGIN NORMAL
# ===============================
class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(
            "login.html",
            erro=None,
            mensagem=None,
            usuario_prefill=""
        )

    def post(self):
        username = self.get_argument("username", "").strip()
        password = self.get_argument("password", "").strip()

        if not username or not password:
            self.render(
                "login.html",
                erro="Preencha todos os campos",
                mensagem=None,
                usuario_prefill=username
            )
            return

        senha_hash = hash_senha(password)

        conn = conectar()
        c = conn.cursor()

        c.execute("""
            SELECT id, username, inicio_curso
            FROM users
            WHERE username=? AND password=? AND ativo=1
        """, (username, senha_hash))

        user = c.fetchone()

        if not user:
            conn.close()
            self.render(
                "login.html",
                erro="Usuário inválido ou bloqueado",
                mensagem=None,
                usuario_prefill=username
            )
            return

        # 🟢 salva início do curso (1ª vez)
        if not user["inicio_curso"]:
            inicio = datetime.now().strftime("%d/%m/%Y")
            c.execute("""
                UPDATE users
                SET inicio_curso = ?
                WHERE id = ?
            """, (inicio, user["id"]))
            conn.commit()

        conn.close()

        self.set_secure_cookie("user", user["username"])
        self.set_secure_cookie("user_id", str(user["id"]))
        self.redirect("/curso")


# ===============================
# LOGIN GOOGLE
# ===============================
class GoogleLoginHandler(
    tornado.web.RequestHandler,
    tornado.auth.GoogleOAuth2Mixin
):
    async def get(self):
        if self.get_argument("code", False):

            token = await self.get_authenticated_user(
                redirect_uri="http://localhost:8080/auth/google",
                code=self.get_argument("code")
            )

            if not token:
                self.redirect("/login")
                return

            user_info = await self.oauth2_request(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                access_token=token["access_token"]
            )

            email = user_info.get("email")
            nome = user_info.get("name", "")

            if not email:
                self.write("Erro: Google não retornou e-mail")
                return

            username = email.split("@")[0]

            conn = conectar()
            c = conn.cursor()

            c.execute("""
                SELECT id, ativo, inicio_curso
                FROM users
                WHERE email=?
            """, (email,))

            row = c.fetchone()

            if not row:
                senha_fake = hash_senha(str(uuid.uuid4()))
                inicio = datetime.now().strftime("%d/%m/%Y")

                c.execute("""
                    INSERT INTO users
                    (username, password, email, ativo, inicio_curso)
                    VALUES (?, ?, ?, 1, ?)
                """, (username, senha_fake, email, inicio))

                user_id = c.lastrowid
            else:
                if row["ativo"] == 0:
                    conn.close()
                    self.write("Conta bloqueada pelo administrador.")
                    return

                user_id = row["id"]

            conn.commit()
            conn.close()

            self.set_secure_cookie("user", username)
            self.set_secure_cookie("user_id", str(user_id))
            self.redirect("/curso")

        else:
            self.authorize_redirect(
                redirect_uri="http://localhost:8080/auth/google",
                client_id=self.settings["google_oauth"]["key"],
                scope=["openid", "email", "profile"],
                response_type="code",
                extra_params={"prompt": "select_account"}
            )


# ===============================
# LOGOUT
# ===============================
class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.clear_cookie("user")
        self.clear_cookie("user_id")
        self.redirect("/login")
