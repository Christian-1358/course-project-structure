import os
import sqlite3
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

# ------------------ FUNÇÕES DE APOIO PROFISSIONAIS ------------------
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

# ------------------ SISTEMA DE CERTIFICADO MASTER ELITE ------------------

class GerarCertificadoHandler(tornado.web.RequestHandler):
    def initialize(self, modulo_id=None):
        self.modulo_id_default = modulo_id

    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    @tornado.web.authenticated
    def get(self, modulo_id=None):
        uid = self.current_user
        mid_raw = modulo_id or self.modulo_id_default
        is_final = str(mid_raw).lower() in ["6", "final", "conclusao"]
        
        conn = conectar(); c = conn.cursor()
        c.execute("SELECT username, nome FROM users WHERE id = ?", (uid,))
        user = c.fetchone()
        if not user: conn.close(); self.redirect("/login"); return

        nome_aluno = (user['nome'] if user['nome'] else user['username']).upper()
        data_atual = datetime.now().strftime('%d/%m/%Y')
        cert_id = hashlib.sha1(f"{uid}-{data_atual}".encode()).hexdigest()[:12].upper()

        # HTML COM DESIGN DE LUXO E POSICIONAMENTO FIXO (ANTI-BUG)
        html_master = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{ size: A4 landscape; margin: 0; }}
                body {{ background-color: #050505; margin: 0; padding: 0; font-family: 'Helvetica', 'Arial', sans-serif; }}
                
                .container {{ 
                    width: 297mm; height: 210mm; background-color: #000; 
                    position: relative; overflow: hidden; 
                }}

                /* Moldura Externa Dupla */
                .frame-outer {{ position: absolute; top: 25px; left: 25px; right: 25px; bottom: 25px; border: 4px solid #d4af37; }}
                .frame-inner {{ position: absolute; top: 10px; left: 10px; right: 10px; bottom: 10px; border: 1px solid rgba(212, 175, 55, 0.3); }}

                /* Conteúdo Centralizado com Alturas Fixas */
                .logo-header {{ position: absolute; top: 60px; width: 100%; text-align: center; color: #FFF; letter-spacing: 12px; font-size: 20px; font-weight: bold; }}
                .logo-header span {{ color: #d4af37; }}

                .main-title {{ position: absolute; top: 95px; width: 100%; text-align: center; font-size: 105px; font-weight: 900; letter-spacing: 20px; color: #d4af37; margin: 0; }}
                .sub-title {{ position: absolute; top: 210px; width: 100%; text-align: center; font-size: 14px; color: #888; letter-spacing: 8px; font-weight: bold; }}

                .cert-text {{ position: absolute; top: 255px; width: 100%; text-align: center; font-size: 22px; color: #FFF; font-style: italic; opacity: 0.9; }}

                .student-name {{ 
                    position: absolute; top: 295px; width: 75%; left: 12.5%; 
                    text-align: center; font-size: 78px; color: #FFF; font-weight: bold; 
                    border-bottom: 3px solid #d4af37; padding-bottom: 8px; 
                }}

                .description {{ 
                    position: absolute; top: 415px; width: 850px; left: 50%; margin-left: -425px; 
                    text-align: center; font-size: 18px; color: #CCC; line-height: 1.7; 
                }}

                /* Grade de Habilidades Profissional */
                .skills-grid {{ 
                    position: absolute; top: 515px; width: 800px; left: 50%; margin-left: -400px; 
                    display: block; border: 1px solid rgba(212, 175, 55, 0.2); 
                    background: rgba(15, 15, 15, 0.8); padding: 20px; 
                }}
                .skill {{ width: 49%; display: inline-block; font-size: 13px; font-weight: bold; color: #d4af37; text-align: center; }}
                .skill span {{ color: #FFF; margin-right: 8px; }}

                /* Rodapé e Assinaturas */
                .signature-box {{ position: absolute; bottom: 85px; width: 280px; border-top: 1px solid #444; text-align: center; font-size: 13px; color: #888; padding-top: 8px; }}
                .sig-left {{ left: 100px; }}
                .sig-right {{ right: 100px; }}

                .date-display {{ position: absolute; bottom: 95px; width: 100%; text-align: center; font-size: 24px; font-weight: 900; color: #FFF; }}
                .verification {{ position: absolute; bottom: 45px; right: 55px; font-size: 10px; color: #222; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="frame-outer">
                    <div class="frame-inner">
                        <div class="logo-header">MESTRE DAS <span>MILHAS</span></div>
                        <h1 class="main-title">CERTIFICADO</h1>
                        <div class="sub-title">EXECUTIVE MASTERY PROGRAM 2026</div>

                        <div class="cert-text">Certificamos com máxima honra que o especialista</div>
                        <div class="student-name">{nome_aluno}</div>

                        <div class="description">
                            Concluiu com excelência todos os módulos técnicos de inteligência financeira aplicados ao mercado de 
                            fidelidade aérea e arbitragem de capital do programa <b>MASTER MILHAS</b>.
                        </div>

                        <div class="skills-grid">
                            <div class="skill"><span>✦</span> ENGENHARIA DE CPM</div>
                            <div class="skill"><span>✦</span> EMISSÕES FIRST CLASS</div>
                            <div class="skill"><span>✦</span> GESTÃO DE SPREAD</div>
                            <div class="skill"><span>✦</span> ARBITRAGEM ELITE</div>
                        </div>

                        <div class="signature-box sig-left">DIRETORIA PEDAGÓGICA</div>
                        <div class="date-display">{data_atual}</div>
                        <div class="signature-box sig-right">MESTRE DAS MILHAS INC.</div>
                        <div class="verification">AUTH_ID: {cert_id}</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        if self.get_argument("download", "0") in ("1", "true"):
            conn.close()
            self.gerar_pdf_file(html_master, f"Certificado_Elite_{uid}.pdf")
        else:
            if is_final: self.render("certificado_final.html", nome=nome_aluno, data=data_atual)
            else: self.write("Use ?download=1 para ver o PDF de luxo.")
            conn.close()

    def gerar_pdf_file(self, html_string, filename):
        pdf = BytesIO()
        HTML(string=html_string).write_pdf(pdf)
        pdf.seek(0)
        self.set_header("Content-Type", "application/pdf")
        self.set_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.write(pdf.read())

# Handlers Administrativos
class LoginDevHandler(tornado.web.RequestHandler):
    def get(self): self.render("painel_dev.html", usuarios=listar_usuarios(), notas=listar_notas_geral(), mensagem=None)

class ForcarNotasHandler(tornado.web.RequestHandler):
    def post(self):
        if forcar_notas_teste(self.get_argument("id")): self.write({"sucesso": True})
        else: self.write({"sucesso": False})

class AlterarStatusHandler(tornado.web.RequestHandler):
    def post(self):
        uid = self.get_argument("id"); st = self.get_argument("ativo")
        conn = conectar(); conn.execute("UPDATE users SET ativo=? WHERE id=?", (st, uid)); conn.commit(); conn.close()
        self.write({"sucesso": True})

class BuscarUsuarioHandler(tornado.web.RequestHandler):
    def get(self): self.render("painel_dev.html", usuarios=listar_usuarios(self.get_argument("filtro", "")), notas=listar_notas_geral(), mensagem="Filtro aplicado")

class ComprasHandler(tornado.web.RequestHandler):
    def get(self):
        conn = conectar(); c = conn.cursor(); c.execute("SELECT * FROM purchases ORDER BY id DESC")
        vendas = [dict(row) for row in c.fetchall()]; conn.close(); self.write({"purchases": vendas})

def criar_tabela(): pass
def criar_usuario_admin_se_nao_existe(): pass


# ------------------ HANDLERS ADICIONAIS DE ADMIN ------------------
class MarcarPagoHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            uid = int(self.get_argument("id"))
        except Exception:
            self.write({"sucesso": False, "mensagem": "id inválido"})
            return

        try:
            conn = conectar(); c = conn.cursor()
            agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("UPDATE users SET pago=1, data_pagamento=?, inicio_curso=?, ativo=1 WHERE id=?", (agora, agora, uid))
            conn.commit(); conn.close()
            self.write({"sucesso": True, "mensagem": "Usuário marcado como pago"})
        except Exception as e:
            self.write({"sucesso": False, "mensagem": str(e)})


def ensure_bloqueio_column():
    try:
        conn = conectar(); c = conn.cursor()
        c.execute("ALTER TABLE users ADD COLUMN bloqueio_motivo TEXT")
        conn.commit(); conn.close()
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


class RemoverPagamentoHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            uid = int(self.get_argument("id"))
        except Exception:
            self.write({"sucesso": False, "mensagem": "id inválido"})
            return

        try:
            conn = conectar(); c = conn.cursor()
            c.execute("UPDATE users SET pago=0, data_pagamento=NULL WHERE id=?", (uid,))
            conn.commit(); conn.close()
            self.write({"sucesso": True, "mensagem": "Pagamento removido"})
        except Exception as e:
            self.write({"sucesso": False, "mensagem": str(e)})


class BloquearUsuarioHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            uid = int(self.get_argument("id"))
            motivo = self.get_argument("motivo", "Bloqueado pelo administrador")
        except Exception:
            self.write({"sucesso": False, "mensagem": "Parâmetros inválidos"})
            return

        try:
            ensure_bloqueio_column()
            conn = conectar(); c = conn.cursor()
            c.execute("UPDATE users SET ativo=0, bloqueio_motivo=? WHERE id=?", (motivo, uid))
            conn.commit(); conn.close()
            self.write({"sucesso": True, "mensagem": "Usuário bloqueado"})
        except Exception as e:
            self.write({"sucesso": False, "mensagem": str(e)})


class DesbloquearUsuarioHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            uid = int(self.get_argument("id"))
        except Exception:
            self.write({"sucesso": False, "mensagem": "id inválido"})
            return

        try:
            conn = conectar(); c = conn.cursor()
            # tenta limpar motivo se coluna existir
            try:
                c.execute("UPDATE users SET ativo=1, bloqueio_motivo=NULL WHERE id=?", (uid,))
            except Exception:
                c.execute("UPDATE users SET ativo=1 WHERE id=?", (uid,))
            conn.commit(); conn.close()
            self.write({"sucesso": True, "mensagem": "Usuário desbloqueado"})
        except Exception as e:
            self.write({"sucesso": False, "mensagem": str(e)})


class ResetarSenhaHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            uid = int(self.get_argument("id"))
        except Exception:
            self.write({"sucesso": False, "mensagem": "id inválido"})
            return

        try:
            conn = conectar(); c = conn.cursor()
            c.execute("SELECT username FROM users WHERE id = ?", (uid,))
            row = c.fetchone()
            if not row:
                conn.close()
                self.write({"sucesso": False, "mensagem": "Usuário não encontrado"})
                return
            username = row["username"]
            nova_hash = hashlib.sha256(username.encode()).hexdigest()
            c.execute("UPDATE users SET password=? WHERE id=?", (nova_hash, uid))
            conn.commit(); conn.close()
            self.write({"sucesso": True, "mensagem": "Senha resetada para o nome de usuário"})
        except Exception as e:
            self.write({"sucesso": False, "mensagem": str(e)})


class AlterarSenhaHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            uid = int(self.get_argument("id"))
            nova = self.get_argument("senha")
        except Exception:
            self.write({"sucesso": False, "mensagem": "Parâmetros inválidos"})
            return

        try:
            # usa SHA256 para compatibilidade com o login
            nova_hash = hashlib.sha256(nova.encode()).hexdigest()
            conn = conectar(); c = conn.cursor()
            c.execute("UPDATE users SET password=? WHERE id=?", (nova_hash, uid))
            conn.commit(); conn.close()
            self.write({"sucesso": True, "mensagem": "Senha alterada com sucesso"})
        except Exception as e:
            self.write({"sucesso": False, "mensagem": str(e)})