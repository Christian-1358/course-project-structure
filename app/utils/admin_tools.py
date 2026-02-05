import sqlite3
import os
import hashlib
import tornado.web
import json
import time
from datetime import datetime
from io import BytesIO
from weasyprint import HTML

# ------------------ CONFIGURAÇÃO DE BANCO ------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(BASE_DIR, "usuarios.db")

def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def hash_senha(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# ------------------ FUNÇÕES DE APOIO ------------------

def registrar_compra(email, user_id=None, metodo="PIX", amount=29.99, status="approved"):
    try:
        conn = conectar(); c = conn.cursor(); ts = int(time.time())
        c.execute("INSERT INTO purchases (user_id, email, metodo, amount, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, email, metodo, amount, status, ts))
        conn.commit(); conn.close()
        return True, "Ok"
    except Exception as e: return False, str(e)

def forcar_notas_teste(user_id):
    try:
        conn = conectar(); c = conn.cursor()
        uid = int(user_id)
        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("DELETE FROM provas_resultado WHERE user_id = ?", (uid,))
        for m in range(1, 6):
            c.execute("INSERT INTO provas_resultado (user_id, modulo, nota, aprovado, data) VALUES (?, ?, 10.0, 1, ?)", (uid, m, agora))
            c.execute(f"UPDATE users SET fim_modulo{m} = ? WHERE id = ?", (agora, uid))
        conn.commit(); conn.close()
        return True
    except: return False

def listar_usuarios(filtro=""):
    conn = conectar(); c = conn.cursor()
    f = f"%{filtro}%" if filtro else "%"
    c.execute("SELECT id, username, email, ativo FROM users WHERE username LIKE ? OR email LIKE ? ORDER BY id DESC", (f, f))
    res = [dict(row) for row in c.fetchall()]; conn.close()
    return res

def listar_notas_geral():
    conn = conectar(); c = conn.cursor()
    try:
        c.execute("SELECT u.username, pr.modulo, pr.nota, pr.data as data_hora FROM provas_resultado pr JOIN users u ON pr.user_id = u.id ORDER BY pr.id DESC LIMIT 50")
        return [dict(row) for row in c.fetchall()]
    except: return []
    finally: conn.close()

# ------------------ HANDLERS ADMIN ------------------

class LoginDevHandler(tornado.web.RequestHandler):
    def get(self): self.render("painel_dev.html", usuarios=listar_usuarios(), notas=listar_notas_geral(), mensagem=None)

class ForcarNotasHandler(tornado.web.RequestHandler):
    def post(self):
        uid = self.get_argument("id")
        if forcar_notas_teste(uid): self.write({"sucesso": True})
        else: self.write({"sucesso": False})

class AlterarStatusHandler(tornado.web.RequestHandler):
    def post(self):
        uid = self.get_argument("id"); st = self.get_argument("ativo")
        conn = conectar(); conn.execute("UPDATE users SET ativo=? WHERE id=?", (st, uid)); conn.commit(); conn.close()
        self.write({"sucesso": True})

class AlterarSenhaHandler(tornado.web.RequestHandler):
    def post(self):
        uid = self.get_argument("id"); pw = self.get_argument("senha")
        conn = conectar(); conn.execute("UPDATE users SET password=? WHERE id=?", (hash_senha(pw), uid)); conn.commit(); conn.close()
        self.write({"sucesso": True})

class ResetarSenhaHandler(tornado.web.RequestHandler):
    def post(self):
        uid = self.get_argument("id"); conn = conectar(); conn.execute("UPDATE users SET password=? WHERE id=?", (hash_senha("123456"), uid)); conn.commit(); conn.close()
        self.write({"sucesso": True})

class DeletarUsuarioHandler(tornado.web.RequestHandler):
    def post(self):
        uid = self.get_argument("id"); conn = conectar(); conn.execute("DELETE FROM users WHERE id=?", (uid,)); conn.commit(); conn.close()
        self.write({"sucesso": True})

class BuscarUsuarioHandler(tornado.web.RequestHandler):
    def get(self):
        f = self.get_argument("filtro", ""); self.render("painel_dev.html", usuarios=listar_usuarios(f), notas=listar_notas_geral(), mensagem=f"Busca: {f}")

class ComprasHandler(tornado.web.RequestHandler):
    def get(self):
        conn = conectar(); c = conn.cursor(); c.execute("SELECT * FROM purchases ORDER BY id DESC")
        vendas = [dict(row) for row in c.fetchall()]; conn.close(); self.write({"purchases": vendas})

# ------------------ SISTEMA DE CERTIFICADO PROTEGIDO E DINÂMICO ------------------

class GerarCertificadoHandler(tornado.web.RequestHandler):
    def get(self, requested_id=None):
        # SEGURANÇA: Obtém o ID do usuário através do cookie seguro. 
        # Ignoramos completamente o 'requested_id' vindo da URL. [cite: 2026-01-20]
        user_id_cookie = self.get_secure_cookie("user_id")
        
        if not user_id_cookie:
            self.redirect("/login")
            return
            
        conn = conectar(); c = conn.cursor()
        # SEGURANÇA: Busca dados apenas do usuário autenticado. [cite: 2026-01-20]
        c.execute("SELECT username, nome, fim_modulo5 FROM users WHERE id = ?", (int(user_id_cookie),))
        user = c.fetchone(); conn.close()

        if not user:
            self.redirect("/login")
            return

        # SEGURANÇA: Se o campo fim_modulo5 estiver vazio, bloqueia. [cite: 2026-01-20]
        if not user['fim_modulo5']:
            self.set_status(403)
            self.write("<h3>Acesso Proibido: Você deve concluir todos os módulos para acessar o certificado.</h3>")
            return

        nome_aluno = (user['nome'] if user['nome'] else user['username']).upper()
        # DATA DINÂMICA: Gera com a data atual do servidor. [cite: 2026-01-20]
        data_atual = datetime.now().strftime('%d/%m/%Y')

        if self.get_argument("download", "0") == "1":
            html_pdf = f"""
            <html>
            <head>
                <style>
                    @page {{ size: A4 landscape; margin: 0; }}
                    body {{ background-color: #000; margin: 0; padding: 0; font-family: 'Helvetica', sans-serif; color: white; }}
                    .bg {{ background-color: #0d0d0d; width: 297mm; height: 210mm; padding: 12mm; box-sizing: border-box; }}
                    .border {{
                        width: 100%; height: 100%;
                        border: 5px double #d4af37;
                        box-sizing: border-box;
                        text-align: center;
                        position: relative;
                        padding: 40px;
                    }}
                    .logo {{ font-size: 20pt; font-weight: bold; letter-spacing: 5px; margin-bottom: 20px; }}
                    .logo span {{ color: #d4af37; }}
                    .title {{ font-size: 60pt; color: #d4af37; font-weight: 900; letter-spacing: 10px; margin: 10px 0; }}
                    .subtitle {{ font-size: 12pt; color: #888; letter-spacing: 4px; text-transform: uppercase; margin-bottom: 40px; }}
                    .intro {{ font-size: 18pt; color: #ccc; font-style: italic; }}
                    .name {{ 
                        margin: 20px auto; font-size: 52pt; font-weight: bold; color: #fff;
                        border-bottom: 3pt solid #d4af37; display: inline-block; padding: 0 60px 10px 60px;
                    }}
                    .desc {{ margin: 30px auto; width: 85%; font-size: 15pt; line-height: 1.6; color: #aaa; }}
                    .ementa-main {{ margin: 20px auto; width: 70%; text-align: center; }}
                    .ementa-title {{ font-size: 11pt; color: #d4af37; letter-spacing: 2pt; margin-bottom: 15px; text-transform: uppercase; font-weight: bold; }}
                    .ementa-grid {{ display: block; background: rgba(212, 175, 55, 0.03); border: 1px solid rgba(212, 175, 55, 0.1); padding: 20px; border-radius: 15px; }}
                    .ementa-item {{ display: inline-block; width: 45%; color: #d4af37; font-size: 10pt; text-align: center; margin: 8px 0; font-weight: bold; }}
                    .footer {{ position: absolute; bottom: 45px; width: 100%; left: 0; color: #d4af37; font-size: 13pt; font-weight: bold; letter-spacing: 3pt; }}
                </style>
            </head>
            <body>
                <div class="bg">
                    <div class="border">
                        <div class="logo">MESTRE DAS <span>MILHAS</span></div>
                        <div class="title">CERTIFICADO</div>
                        <div class="subtitle">Formação Profissional em Arbitragem</div>
                        <div class="intro">Certificamos com distinção que o especialista</div>
                        <div class="name">{nome_aluno}</div>
                        <div class="desc">
                            Concluiu com êxito os treinamentos avançados do programa <b>MASTER MILHAS 2026</b>, 
                            conquistando sua licença de operação profissional.
                        </div>
                        <div class="ementa-main">
                            <div class="ementa-title">— Conteúdos Aprendidos —</div>
                            <div class="ementa-grid">
                                <div class="ementa-item">✔ ENGENHARIA DE CPM AVANÇADA</div>
                                <div class="ementa-item">✔ GESTÃO ESTRATÉGICA DE CPFs</div>
                                <div class="ementa-item">✔ EMISSÕES AWARD INTERNACIONAIS</div>
                                <div class="ementa-item">✔ ARBITRAGEM E COMPRA BONIFICADA</div>
                            </div>
                        </div>
                        <div class="footer">{data_atual}</div>
                    </div>
                </div>
            </body>
            </html>
            """
            pdf_file = BytesIO()
            HTML(string=html_pdf).write_pdf(pdf_file)
            pdf_file.seek(0)
            self.set_header("Content-Type", "application/pdf")
            self.set_header("Content-Disposition", f'attachment; filename="Certificado_{nome_aluno}.pdf"')
            self.write(pdf_file.read())
        else:
            self.render("certificado_final.html", nome=nome_aluno)

def criar_tabela(): pass
def criar_usuario_admin_se_nao_existe(): pass