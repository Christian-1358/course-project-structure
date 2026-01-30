import tornado.web
import sqlite3
import os
from datetime import datetime

# Configuração de Caminhos Profissionais
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class ProvaHandler(tornado.web.RequestHandler):
    def get_user(self, user_id):
        conn = conectar()
        try:
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return user
        finally:
            conn.close()

    def validar_aprovacao_previa(self, user_id):
        user = self.get_user(user_id)
        if not user: return False
        # Verifica se os 5 módulos foram concluídos
        modulos = ['fim_modulo1', 'fim_modulo2', 'fim_modulo3', 'fim_modulo4', 'fim_modulo5']
        return all(user[m] is not None and user[m] != "" for m in modulos)

    def get(self, modulo):
        user_id_cookie = self.get_secure_cookie("user_id")
        if not user_id_cookie: return self.redirect("/login")
        user_id = int(user_id_cookie.decode())
        
        user = self.get_user(user_id)
        modulo_num = int(modulo)

        # Trava de Segurança para Prova Final
        if modulo_num == 6 and not self.validar_aprovacao_previa(user_id):
            self.write("<script>alert('❌ BLOQUEADO: Conclua os 5 módulos com nota > 7 primeiro!'); window.location.href='/curso';</script>")
            return

        paginas = {
            "1":"prova.html", "2":"prova2.html", "3":"prova3.html",
            "4":"prova4.html", "5":"prova5.html", "6":"prova6.html"
        }
        
        # Envio seguro de variáveis para o template
        self.render(
            paginas.get(str(modulo), "prova.html"), 
            modulo=modulo_num, 
            nome_usuario=user['nome'] if user else "Aluno",
            nota_final=user['nota_final'] if (user and 'nota_final' in user.keys()) else 0,
            user_id=user_id
        )

    def post(self, modulo):
        user_id_cookie = self.get_secure_cookie("user_id")
        user_id = int(user_id_cookie.decode())
        modulo_num = int(modulo)

        # Gabaritos Oficiais
        gabaritos = {
            1: {"q1":"a","q2":"c","q3":"b","q4":"d","q5":"a","q6":"c","q7":"b","q8":"a","q9":"d","q10":"c"},
            2: {"q1":"b","q2":"a","q3":"d","q4":"c","q5":"b","q6":"a","q7":"d","q8":"b","q9":"c","q10":"a"},
            3: {"q1":"c","q2":"b","q3":"d","q4":"a","q5":"c","q6":"b","q7":"d","q8":"a","q9":"c","q10":"b"},
            4: {"q1":"d","q2":"a","q3":"c","q4":"b","q5":"d","q6":"a","q7":"c","q8":"b","q9":"d","q10":"a"},
            5: {"q1":"b","q2":"c","q3":"a","q4":"d","q5":"b","q6":"c","q7":"a","q8":"d","q9":"b","q10":"c"},
            
            
            6: { # Gabarito Final 50 Questões
                "q1":"a","q2":"c","q3":"b","q4":"d","q5":"a","q6":"c","q7":"b","q8":"a","q9":"d","q10":"c",
                "q11":"b","q12":"a","q13":"d","q14":"c","q15":"b","q16":"a","q17":"d","q18":"b","q19":"c","q20":"a",
                "q21":"c","q22":"b","q23":"d","q24":"a","q25":"c","q26":"b","q27":"d","q28":"a","q29":"c","q30":"b",
                "q31":"d","q32":"a","q33":"c","q34":"b","q35":"d","q36":"a","q37":"c","q38":"b","q39":"d","q40":"a",
                "q41":"b","q42":"c","q43":"a","q44":"d","q45":"b","q46":"c","q47":"a","q48":"d","q49":"b","q50":"c"
            }
        }

        gabarito_atual = gabaritos.get(modulo_num, {})
        total_qs = 50 if modulo_num == 6 else 10
        minimo = 40 if modulo_num == 6 else 7

        acertos = sum(1 for i in range(1, total_qs + 1) if self.get_body_argument(f"q{i}", "") == gabarito_atual.get(f"q{i}"))

        if acertos >= minimo:
            data_fim = datetime.now().strftime("%d/%m/%Y")
            conn = conectar()
            c = conn.cursor()
            try:
                if modulo_num == 6:
                    c.execute("UPDATE users SET certificado_mestre = ?, nota_final = ? WHERE id = ?", (data_fim, acertos, user_id))
                    url = "/certificado/final"
                else:
                    c.execute(f"UPDATE users SET fim_modulo{modulo_num} = ? WHERE id = ?", (data_fim, user_id))
                    url = f"/certificado/{modulo_num}"
                conn.commit()
                self.redirect(url)
            finally:
                conn.close()
        else:
            self.write(f"<script>alert('Nota: {acertos}/{total_qs}. Estude mais e tente novamente!'); window.location.href='/curso';</script>")