import tornado.web
import sqlite3
import hashlib
import random
import os
import datetime
import yagmail

# ================== CAMINHOS ==================
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

# ================== EMAIL (GMAIL) ==================
EMAIL_USER = "recuperar.curso@gmail.com"
EMAIL_PASS = "smaw uhli vhdi ywff"  # senha de app do Gmail

# ================== FUNÇÕES ==================
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

# ================== HANDLER ==================
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

        # ================== PASSO 1: ENVIAR CÓDIGO ==================
        if email and not token:
            c.execute("SELECT id FROM users WHERE email=?", (email,))
            user = c.fetchone()

            if user:
                user_id = user[0]
                codigo = str(random.randint(100000, 999999))
                expira = (
                    datetime.datetime.utcnow()
                    + datetime.timedelta(minutes=15)
                ).isoformat()

                c.execute(
                    "DELETE FROM password_reset WHERE user_id=?",
                    (user_id,)
                )

                c.execute("""
                    INSERT INTO password_reset (user_id, token, expires_at)
                    VALUES (?, ?, ?)
                """, (user_id, codigo, expira))

                conn.commit()

                try:
                    yag = yagmail.SMTP(
                        user=EMAIL_USER,
                        password=EMAIL_PASS,
                        host="smtp.gmail.com",
                        port=587,
                        smtp_starttls=True,
                        smtp_ssl=False
                    )

                    html = f"""
                    <div style="font-family:Arial;background:#f4f6f8;padding:20px;">
                      <div style="max-width:500px;margin:auto;background:#fff;padding:25px;border-radius:8px;">
                        <h2>Recuperação de Senha</h2>
                        <p>Use o código abaixo para redefinir sua senha:</p>
                        <div style="font-size:22px;text-align:center;padding:15px;background:#eee;border-radius:6px;">
                          <strong>{codigo}</strong>
                        </div>
                        <p>Este código expira em 15 minutos.</p>
                        <p style="font-size:12px;color:#777;">
                          Curso Online — mensagem automática
                        </p>
                      </div>
                    </div>
                    """

                    yag.send(
                        to=email,
                        subject="Recuperação de Senha",
                        contents=html
                    )

                except Exception as e:
                    print("ERRO AO ENVIAR EMAIL:", e)

            self.render(
                "recuperar_senha.html",
                erro=None,
                sucesso="Se o e-mail existir, enviamos um código de verificação."
            )
            conn.close()
            return

        # ================== PASSO 2: ALTERAR SENHA ==================
        if token and nova_senha:
            if len(nova_senha) < 5:
                self.render(
                    "recuperar_senha.html",
                    erro="A senha deve ter no mínimo 5 caracteres.",
                    sucesso=None
                )
                conn.close()
                return

            agora = datetime.datetime.utcnow().isoformat()

            c.execute("""
                SELECT user_id FROM password_reset
                WHERE token=? AND expires_at > ?
            """, (token, agora))

            row = c.fetchone()

            if not row:
                self.render(
                    "recuperar_senha.html",
                    erro="Código inválido ou expirado.",
                    sucesso=None
                )
                conn.close()
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
                sucesso="Senha alterada com sucesso. Volte ao login."
            )
            return

        conn.close()
        self.render(
            "recuperar_senha.html",
            erro="Preencha todos os campos.",
            sucesso=None
        )
