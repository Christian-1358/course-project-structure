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
# Localiza o banco de dados na raiz do projeto
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
        # Simula aprovação nos 5 módulos
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

# ------------------ HANDLERS ADMIN (TODOS INCLUSOS) ------------------

class LoginDevHandler(tornado.web.RequestHandler):
    def get(self): 
        self.render("painel_dev.html", usuarios=listar_usuarios(), notas=listar_notas_geral(), mensagem=None)

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
    """ Resolve o erro de ImportError no server.py """
    def get(self):
        f = self.get_argument("filtro", "")
        self.render("painel_dev.html", usuarios=listar_usuarios(f), notas=listar_notas_geral(), mensagem=f"Busca: {f}")

class ComprasHandler(tornado.web.RequestHandler):
    def get(self):
        conn = conectar(); c = conn.cursor(); c.execute("SELECT * FROM purchases ORDER BY id DESC")
        vendas = [dict(row) for row in c.fetchall()]; conn.close(); self.write({"purchases": vendas})

# ------------------ SISTEMA DE CERTIFICADO (RESOLVIDO) ------------------

class GerarCertificadoHandler(tornado.web.RequestHandler):
    
    def get_current_user(self):
        """ Essencial para o Tornado reconhecer o login """
        uid = self.get_secure_cookie("user_id")
        if uid:
            try: return int(uid.decode())
            except: return None
        return None

    @tornado.web.authenticated
    def get(self, modulo_id):
        uid = self.current_user
        try:
            mid = int(modulo_id)
        except:
            self.write("ID de módulo inválido."); return

        download_arg = self.get_argument("download", "0")
        download = download_arg in ("1", "true", "True", "yes")
        
        conn = conectar(); c = conn.cursor()
        c.execute("SELECT username, nome, inicio_curso, fim_modulo5 FROM users WHERE id = ?", (uid,))
        user = c.fetchone()

        if not user:
            conn.close(); self.redirect("/login"); return

        nome_aluno = (user['nome'] if user['nome'] else user['username']).upper()
        data_inicio = user['inicio_curso'] or "01/01/2026"

        # --- FLUXO MÓDULOS 1 A 5 (Certificado por Módulo) ---
        if 1 <= mid <= 5:
            r = c.execute("SELECT data FROM provas_resultado WHERE user_id = ? AND modulo = ? ORDER BY id DESC", (uid, mid)).fetchone()
            conn.close()

            if not r:
                self.write("<h3>Acesso Negado: Conclua a prova deste módulo primeiro.</h3>")
                return
            
            data_fim = r['data'].split()[0]
            ementas = {
                1: "Visão Geral 2026, CPM, Dicionário do Milheiro",
                2: "Cartões, Anuidade Zero, Salas VIP",
                3: "Compra de Pontos, Bônus, Estratégia 10x1",
                4: "Executiva, Stopover, Iberia Plus",
                5: "Venda de Milhas, Gestão de Lucro, IR"
            }
            ementa_txt = ementas.get(mid, "")

            if download:
                html = self.render_string("certificado.html", nome=nome_aluno, modulo=mid, ementa=ementa_txt, inicio=data_inicio, fim=data_fim, is_pdf=True).decode()
                self.gerar_pdf_file(html, f"Certificado_Modulo_{mid}.pdf")
            else:
                self.render("certificado.html", nome=nome_aluno, modulo=mid, ementa=ementa_txt, inicio=data_inicio, fim=data_fim, is_pdf=False)
            return

        # --- FLUXO MÓDULO 6 (Certificado Final Luxuoso) ---
        elif mid == 6:
            if not user['fim_modulo5']:
                conn.close()
                self.write("<script>alert('Conclua todos os módulos primeiro!'); location='/curso'</script>")
                return
            
            conn.close()
            data_atual = datetime.now().strftime('%d/%m/%Y')

            if download:
                # Layout do Certificado Final direto no código para evitar erros de template
                html_final = f"""
                <html>
                <head>
                    <style>
                        @page {{ size: A4 landscape; margin: 0; }}
                        body {{ background-color: #000; margin: 0; padding: 0; font-family: 'Helvetica', sans-serif; color: white; }}
                        .bg {{ background-color: #0d0d0d; width: 297mm; height: 210mm; padding: 12mm; box-sizing: border-box; }}
                        .border {{ width: 100%; height: 100%; border: 5px double #d4af37; text-align: center; padding: 40px; position: relative; box-sizing: border-box; }}
                        .logo {{ font-size: 20pt; font-weight: bold; letter-spacing: 5px; color: white; }}
                        .logo span {{ color: #d4af37; }}
                        .title {{ font-size: 60pt; color: #d4af37; font-weight: 900; margin: 20px 0; }}
                        .name {{ font-size: 52pt; font-weight: bold; border-bottom: 3pt solid #d4af37; display: inline-block; padding: 0 40px; }}
                        .footer {{ position: absolute; bottom: 40px; width: 100%; left: 0; color: #d4af37; font-size: 14pt; }}
                    </style>
                </head>
                <body>
                    <div class="bg"><div class="border">
                        <div class="logo">MESTRE DAS <span>MILHAS</span></div>
                        <div class="title">CERTIFICADO FINAL</div>
                        <div class="name">{nome_aluno}</div>
                        <div class="footer">{data_atual}</div>
                    </div></div>
                </body>
                </html>
                """
                self.gerar_pdf_file(html_final, f"Certificado_Final_{nome_aluno}.pdf")
            else:
                self.render("certificado_final.html", nome=nome_aluno, data=data_atual)
            return

        conn.close()
        self.set_status(404)

    def gerar_pdf_file(self, html_string, filename):
        pdf = BytesIO()
        HTML(string=html_string).write_pdf(pdf)
        pdf.seek(0)
        self.set_header("Content-Type", "application/pdf")
        self.set_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.write(pdf.read())

def criar_tabela(): pass
def criar_usuario_admin_se_nao_existe(): pass