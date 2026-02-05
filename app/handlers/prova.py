import tornado.web
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

def conectar():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    return conn

class ProvaHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return uid.decode() if uid else None

    @tornado.web.authenticated
    def get(self, modulo):
        user_id = self.current_user
        mod = int(modulo)
        
        # --- TRAVA DE SEGURANÇA: Impede pular módulos via URL ---
        if mod > 1:
            conn = conectar()
            anterior = conn.execute("SELECT nota FROM provas_resultado WHERE user_id = ? AND modulo = ?", (user_id, mod-1)).fetchone()
            conn.close()
            if not anterior or anterior['nota'] < 6:
                self.write("<script>alert('Você precisa passar na prova anterior primeiro!'); window.location='/curso';</script>")
                return

        conn = conectar()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        
        paginas = {1:"prova.html", 2:"prova2.html", 3:"prova3.html", 4:"prova4.html", 5:"prova5.html", 6:"prova_final.html"}
        self.render(paginas.get(mod, "prova.html"), modulo=mod, nome_usuario=user["username"])

    @tornado.web.authenticated
    def post(self, modulo):
        user_id = self.current_user; mod = int(modulo)
        
        gabaritos = {
            1: {"q1":"b","q2":"b","q3":"c","q4":"a","q5":"b","q6":"d","q7":"a","q8":"c","q9":"a","q10":"d"},
            2: {"q1":"a","q2":"d","q3":"b","q4":"c","q5":"a","q6":"b","q7":"d","q8":"a","q9":"c","q10":"b"},            
            3: {"q1":"c","q2":"b","q3":"a","q4":"d","q5":"c","q6":"a","q7":"b","q8":"d","q9":"a","q10":"c"},
            4: {"q1":"b","q2":"a","q3":"c","q4":"d","q5":"b","q6":"a","q7":"c","q8":"d","q9":"b","q10":"a"},
            5: {"q1":"b","q2":"c","q3":"a","q4":"d","q5":"b","q6":"c","q7":"a","q8":"d","q9":"b","q10":"c"},
            6: { # Gabarito Master 50 Questões
                "q1":"a","q2":"c","q3":"b","q4":"d","q5":"a","q6":"c","q7":"b","q8":"a","q9":"d","q10":"c",
                "q11":"b","q12":"a","q13":"d","q14":"c","q15":"b","q16":"a","q17":"d","q18":"b","q19":"c","q20":"a",
                "q21":"c","q22":"b","q23":"d","q24":"a","q25":"c","q26":"b","q27":"d","q28":"a","q29":"c","q30":"b",
                "q31":"d","q32":"a","q33":"c","q34":"b","q35":"d","q36":"a","q37":"c","q38":"b","q39":"d","q40":"a",
                "q41":"b","q42":"c","q43":"a","q44":"d","q45":"b","q46":"c","q47":"a","q48":"d","q49":"b","q50":"c"
            }
        }

        total = 50 if mod == 6 else 10
        minimo = 35 if mod == 6 else 6 
        acertos = sum(1 for i in range(1, total + 1) if self.get_body_argument(f"q{i}", "") == gabaritos.get(mod, {}).get(f"q{i}"))

        if acertos < minimo:
            self.write(f"<script>alert('Sua nota: {acertos}. Você precisa de {minimo} para passar.'); window.location='/prova/{mod}';</script>")
            return

        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        conn = conectar(); c = conn.cursor()
        
        # Salva o resultado
        c.execute("INSERT INTO provas_resultado (user_id, modulo, nota, data) VALUES (?, ?, ?, ?)", (user_id, mod, float(acertos), agora))
        
        # Se for a PROVA 5 ou 6, atualiza o fim_modulo5 para liberar o certificado master
        if mod >= 5:
            c.execute("UPDATE users SET fim_modulo5 = ? WHERE id = ?", (agora, user_id))
        
        conn.commit(); conn.close()

        # --- LÓGICA DE REDIRECIONAMENTO ---
        if mod == 6:
            # Se terminou a PROVA FINAL (master), vai para o certificado completo
            self.redirect("/gerar_certificado_final?download=1")
        else:
            # Se for apenas um módulo (1, 2, 3, 4), volta para o curso com mensagem de sucesso
            # (Ou você pode criar uma página simples de 'Parabéns' para cada módulo)
            self.write(f"<script>alert('Parabéns! Você concluiu o Módulo {mod}.'); window.location='/curso';</script>")