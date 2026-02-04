import tornado.web
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class ProvaHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return uid.decode() if uid else None

    def get_user(self, user_id):
        conn = conectar()
        try:
            return conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        finally:
            conn.close()

    def validar_modulos(self, user):
        for i in range(1, 6):
            if not user[f"fim_modulo{i}"]:
                return False
        return True

    @tornado.web.authenticated
    def get(self, modulo):
        user_id = self.current_user
        user = self.get_user(user_id)
        modulo = int(modulo)

        if modulo == 6 and not self.validar_modulos(user):
            self.write("Acesso negado: conclua todos os módulos antes da prova final.")
            return

        paginas = {
            1: "prova.html",
            2: "prova2.html",
            3: "prova3.html",
            4: "prova4.html",
            5: "prova5.html",
            6: "prova6.html",
        }

        self.render(
            paginas.get(modulo, "prova.html"),
            modulo=modulo,
            nome_usuario=user["nome"] or user["username"]
        )

    @tornado.web.authenticated
    def post(self, modulo):
        user_id = self.current_user
        modulo = int(modulo)

        gabaritos = {
            1: {"q1":"b","q2":"b","q3":"c","q4":"a","q5":"b","q6":"d","q7":"a","q8":"c","q9":"a","q10":"d"},
            2: {"q1":"b","q2":"a","q3":"d","q4":"c","q5":"b","q6":"a","q7":"d","q8":"b","q9":"c","q10":"a"},
            3: {"q1":"c","q2":"b","q3":"d","q4":"a","q5":"c","q6":"b","q7":"d","q8":"a","q9":"c","q10":"b"},
            4: {"q1":"d","q2":"a","q3":"c","q4":"b","q5":"d","q6":"a","q7":"c","q8":"b","q9":"d","q10":"a"},
            5: {"q1":"b","q2":"c","q3":"a","q4":"d","q5":"b","q6":"c","q7":"a","q8":"d","q9":"b","q10":"c"},
            6: {f"q{i}": v for i, v in enumerate(
                ["a","c","b","d","a","c","b","a","d","c",
                 "b","a","d","c","b","a","d","b","c","a",
                 "c","b","d","a","c","b","d","a","c","b",
                 "d","a","c","b","d","a","c","b","d","a",
                 "b","c","a","d","b","c","a","d","b","c"], start=1)}
        }

        total = 50 if modulo == 6 else 10
        minimo = 35 if modulo == 6 else 7
        gabarito = gabaritos[modulo]

        acertos = sum(
            1 for i in range(1, total + 1)
            if self.get_body_argument(f"q{i}", "") == gabarito.get(f"q{i}")
        )

        if acertos < minimo:
            self.write(f"Sua nota foi {acertos}/{total}. Reprovado.")
            return

        data = datetime.now().strftime("%d/%m/%Y")
        conn = conectar()
        try:
            c = conn.cursor()

            if modulo == 6:
                c.execute("UPDATE users SET fim_curso=? WHERE id=?", (data, user_id))
            else:
                c.execute(f"UPDATE users SET fim_modulo{modulo}=? WHERE id=?", (data, user_id))

            c.execute("""
                INSERT INTO provas_resultado (user_id, modulo, nota, aprovado, data)
                VALUES (?, ?, ?, 1, ?)
            """, (user_id, modulo, acertos, data))

            conn.commit()
            self.redirect(f"/certificado/{modulo}")

        finally:
            conn.close()
