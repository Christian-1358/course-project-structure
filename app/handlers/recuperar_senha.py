import tornado.web
import sqlite3
import hashlib
import uuid
import os
import datetime

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")


def conectar():
    return sqlite3.connect(DB_PATH)


def hash_senha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def criar_tabela_tokens():
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS password_reset (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()



class RecuperarSenhaHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("recuperar_senha.html", erro=None, sucesso=None)

    def post(self):
        criar_tabela_tokens()

        email = self.get_argument("email", "").strip()
        token = self.get_argument("token", "").strip()
        nova_senha = self.get_argument("nova_senha", "").strip()

        conn = conectar()
        c = conn.cursor()

        

        if email and not token and not nova_senha:
            c.execute("SELECT id FROM users WHERE email=?", (email,))
            user = c.fetchone()

            if not user:
                self.render(
                    "recuperar_senha.html",
                    erro="E-mail não encontrado",
                    sucesso=None
                )
                return

            user_id = user[0]
            token = str(uuid.uuid4())
            expira = (datetime.datetime.utcnow() + datetime.timedelta(minutes=15)).isoformat()

            c.execute(
                "INSERT INTO password_reset (user_id, token, expires_at) VALUES (?, ?, ?)",
                (user_id, token, expira)
            )
            conn.commit()
            conn.close()

            self.render(
                "recuperar_senha.html",
                erro=None,
                sucesso=f"Token gerado (teste): {token}"
            )
            return

    
        if token and nova_senha:
            agora = datetime.datetime.utcnow().isoformat()

            c.execute("""
                SELECT user_id FROM password_reset
                WHERE token=? AND expires_at > ?
            """, (token, agora))
            row = c.fetchone()

            if not row:
                self.render(
                    "recuperar_senha.html",
                    erro="Token inválido ou expirado",
                    sucesso=None
                )
                return

            user_id = row[0]
            senha_hash = hash_senha(nova_senha)

            c.execute(
                "UPDATE users SET password=? WHERE id=?",
                (senha_hash, user_id)
            )
            c.execute(
                "DELETE FROM password_reset WHERE user_id=?",
                (user_id,)
            )

            conn.commit()
            conn.close()

            self.render(
                "recuperar_senha.html",
                erro=None,
                sucesso="Senha redefinida com sucesso! Faça login."
            )
            return

        conn.close()
        self.render(
            "recuperar_senha.html",
            erro="Dados inválidos",
            sucesso=None
        )
