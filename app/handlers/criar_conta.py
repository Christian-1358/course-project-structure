import tornado.web
import sqlite3
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(BASE_DIR, "usuarios.db")


def conectar():
    conn = sqlite3.connect(DB)
    return conn


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


class CriarContaHandler(tornado.web.RequestHandler):

    def get(self):
        self.render(
            "criar_conta.html",
            erro=None,
            usuario_prefill="",
            email_prefill=""
        )

    def post(self):
        usuario = self.get_argument("usuario").strip()
        email = self.get_argument("email").strip()
        senha = self.get_argument("senha")

        if not usuario or not email or not senha:
            return self.render(
                "criar_conta.html",
                erro="Preencha todos os campos.",
                usuario_prefill=usuario,
                email_prefill=email
            )

        conn = conectar()
        c = conn.cursor()

        try:
            c.execute(
                "INSERT INTO users (username, password, email, ativo) VALUES (?, ?, ?, 1)",
                (usuario, hash_senha(senha), email)
            )
            conn.commit()
            conn.close()

            self.redirect("/login")

        except sqlite3.IntegrityError:
            conn.close()
            self.render(
                "criar_conta.html",
                erro="Usuário ou email já existe.",
                usuario_prefill=usuario,
                email_prefill=email
            )
