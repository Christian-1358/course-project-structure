import tornado.web
import sqlite3
from datetime import datetime

DB = "usuarios.db"


def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn
import tornado.web
import sqlite3
from datetime import datetime

DB = "usuarios.db"


def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn
import tornado.web
import sqlite3
import os
from datetime import datetime

# Localização profissional do banco [cite: 2026-01-20]
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class ProvaHandler(tornado.web.RequestHandler):
    def get(self, modulo):
        # Mapeamento profissional de arquivos [cite: 2026-01-20]
        paginas = {
            "1": "prova.html",
            "2": "prova2.html",
            "3": "prova3.html",
            "4": "prova4.html",
            "5": "prova5.html"
        }
        arquivo = paginas.get(str(modulo), "prova.html")
        self.render(arquivo, modulo=int(modulo))

    def post(self, modulo):
        user_id_cookie = self.get_secure_cookie("user_id")
        if not user_id_cookie: 
            return self.redirect("/login")

        user_id = int(user_id_cookie.decode())
        modulo = int(modulo)
        
        # Gabaritos Oficiais Elite [cite: 2026-01-20]
        gabaritos = {
            1: {"q1":"b","q2":"b","q3":"c","q4":"a","q5":"b","q6":"d","q7":"a","q8":"c","q9":"a","q10":"d"},
            2: {"q1":"a","q2":"d","q3":"b","q4":"c","q5":"a","q6":"b","q7":"d","q8":"a","q9":"c","q10":"b"},
            3: {"q1":"c","q2":"b","q3":"a","q4":"d","q5":"c","q6":"a","q7":"b","q8":"d","q9":"a","q10":"c"},
            4: {"q1":"d","q2":"c","q3":"b","q4":"a","q5":"d","q6":"c","q7":"b","q8":"a","q9":"d","q10":"b"},
            5: {"q1":"b","q2":"a","q3":"d","q4":"c","q5":"b","q6":"a","q7":"d","q8":"c","q9":"b","q10":"a"}
        }

        gabarito_atual = gabaritos.get(modulo, {})
        nota = 0
        
        for i in range(1, 11):
            resposta = self.get_body_argument(f"q{i}", None)
            if resposta == gabarito_atual.get(f"q{i}"):
                nota += 1

        if nota >= 7:
            data_fim = datetime.now().strftime("%d/%m/%Y")
            conn = conectar()
            c = conn.cursor()
            
            try:
                # Atualiza a coluna dinâmica [cite: 2026-01-20]
                query = f"UPDATE users SET fim_modulo{modulo} = ? WHERE id = ?"
                c.execute(query, (data_fim, user_id))
                conn.commit()
            except sqlite3.OperationalError:
                # Caso a coluna não exista, avisa o admin em vez de crashar
                conn.close()
                return self.write(f"<h3>Erro: Coluna fim_modulo{modulo} não existe no banco. Execute o script de migração.</h3>")
            
            conn.close()
            # Redirecionamento dinâmico CORRIGIDO [cite: 2026-01-20]
            self.redirect(f"/certificado/{modulo}")
        else:
            self.redirect(f"/recuperacao/{modulo}") 