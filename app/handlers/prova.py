import tornado.web
import sqlite3
import os
from datetime import datetime
from app.utils.security import set_flow_allowed_if_referer, consume_flow_allowed


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def validar_provas_anteriores(user_id, modulo_atual):
    """
    Valida se o usuário passou em todas as provas anteriores.
    Retorna True se passou em todas, False caso contrário.
    """
    if modulo_atual <= 1:
        return True  # Primeira prova não tem pré-requisitos
    
    conn = conectar()
    # Verifica todas as provas de 1 até modulo_atual - 1
    for mod in range(1, modulo_atual):
        resultado = conn.execute(
            "SELECT nota FROM provas_resultado WHERE user_id = ? AND modulo = ?", 
            (user_id, mod)
        ).fetchone()
        
        # Se não completou a prova ou nota < 6, bloqueia
        if not resultado or resultado['nota'] < 6:
            conn.close()
            return False
    
    conn.close()
    return True

class ProvaHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return uid.decode() if uid else None

    @tornado.web.authenticated
    def get(self, modulo):
        user_id = self.current_user
        mod = int(modulo)
        
        # Central verify: autenticado, pago e fluxo válido
        from app.utils.security import verify_flow_and_payment
        if not verify_flow_and_payment(self, 'prova', mod):
            return

        # --- TRAVA DE SEGURANÇA: Validar todas as provas anteriores ---
        # Esta é a validação correta: usuário pode acessar a prova se passou nas anteriores
        if not validar_provas_anteriores(user_id, mod):
            self.write("<script>alert('Você precisa passar em todas as provas anteriores com nota >= 6 para continuar!'); window.location='/curso';</script>")
            return

        conn = conectar()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        
        paginas = {1:"prova.html", 2:"prova2.html", 3:"prova3.html", 4:"prova4.html", 5:"prova5.html", 6:"prova_final.html"}
        self.render(paginas.get(mod, "prova.html"), modulo=mod, nome_usuario=user["username"])

    @tornado.web.authenticated
    def post(self, modulo):
        user_id = self.current_user
        mod = int(modulo)
        
        # Central verify: autenticado, pago e fluxo válido
        from app.utils.security import verify_flow_and_payment
        if not verify_flow_and_payment(self, 'prova', mod):
            return

        # --- TRAVA DE SEGURANÇA: Validar todas as provas anteriores ---
        if not validar_provas_anteriores(user_id, mod):
            self.write("<script>alert('Você precisa passar em todas as provas anteriores com nota >= 6 para continuar!'); window.location='/curso';</script>")
            return
        
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
            # registrar tentativa falhada para controle de recuperação
            try:
                from app.utils.recuperacao_utils import increment_attempt
                increment_attempt(int(user_id), mod)
            except Exception:
                pass

            self.write(f"<script>alert('Sua nota: {acertos}. Você precisa de {minimo} para passar.'); window.location='/prova/{mod}';</script>")
            return

        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        conn = conectar()
        c = conn.cursor()
        
        # Salva o resultado
        c.execute("INSERT INTO provas_resultado (user_id, modulo, nota, data) VALUES (?, ?, ?, ?)", (user_id, mod, float(acertos), agora))
        
        # Se for a PROVA 5 ou 6, libera o certificado final
        if mod >= 5:
            c.execute("UPDATE users SET fim_modulo5 = ? WHERE id = ?", (agora, user_id))
        
        conn.commit()
        conn.close()

        # Redirecionamento dinâmico conforme o módulo
        if mod == 6:
            self.redirect("/certificado/6?download=1")
        else:
            self.redirect(f"/certificado/{mod}?download=1")