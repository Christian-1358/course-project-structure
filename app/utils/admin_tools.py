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
            try:
                c.execute(f"UPDATE users SET fim_modulo{m} = ? WHERE id = ?", (agora, uid))
            except Exception:
                # coluna não existe no esquema atual, ignora
                pass

        # Tenta definir flags de módulos e nota final / certificado e marcar como pago
        agora_iso = agora
        try:
            c.execute("UPDATE users SET nota_final = ?, certificado_fin = ?, pago = 1, data_pagamento = ?, inicio_curso = ? WHERE id = ?", (10, 1, agora_iso, agora_iso, uid))
        except Exception:
            # tenta menos colunas se esquema diferente
            try:
                c.execute("UPDATE users SET certificado_fin = ? WHERE id = ?", (1, uid))
            except Exception:
                pass
        try:
            c.execute("UPDATE users SET modulo_1 = 1, modulo_2 = 1, modulo_3 = 1, modulo_4 = 1, modulo_5 = 1 WHERE id = ?", (uid,))
        except Exception:
            pass
        conn.commit(); conn.close()
        return True, None
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        return False, str(e)

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
        mid_raw = str(modulo_id or self.modulo_id_default).lower()
        
        # Identifica se é o certificado final
        is_final = mid_raw in ["6", "final", "conclusao"]
        
        # Converte para INT para os IFs do HTML não quebrarem
        try:
            modulo_int = int(mid_raw) if mid_raw.isdigit() else 6
        except:
            modulo_int = 6

        # Busca dados do usuário (apenas colunas que existem: id, username, nome)
        conn = conectar()
        c = conn.cursor()
        c.execute("SELECT username, nome FROM users WHERE id = ?", (uid,))
        user = c.fetchone()
        conn.close()

        if not user:
            self.redirect("/login")
            return

        # Tratamento de dados
        nome_aluno = (user['nome'] if user['nome'] else user['username']).upper()
        data_atual = datetime.now().strftime('%d/%m/%Y')
        
        # Define ementa e carga horária por tipo de módulo
        if is_final:
            ementa_texto = "FORMAÇÃO ESPECIALISTA EM MILHAS AÉREAS"
            carga_horaria = "40h"
            template_alvo = "certificado_final.html"
        else:
            ementa_texto = f"MÓDULO {modulo_int} - EXECUTIVO DE MILHAS"
            carga_horaria = "5h"
            template_alvo = "certificado.html"

        # Renderização com o KIT COMPLETO de variáveis para matar qualquer NameError
        return self.render(
            template_alvo,
            nome=nome_aluno,
            data=data_atual,
            modulo=modulo_int,
            ementa=ementa_texto,
            inicio=data_atual,    # Data de início (usando atual por segurança)
            fim=data_atual,       # <--- CORRIGIDO: Variável 'fim' adicionada aqui
            horas=carga_horaria   # Carga horária
        )

    def gerar_pdf_file(self, html_string, filename):
        from weasyprint import HTML
        from io import BytesIO
        pdf = BytesIO()
        HTML(string=html_string).write_pdf(pdf)
        pdf.seek(0)
        self.set_header("Content-Type", "application/pdf")
        self.set_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.write(pdf.read())
        self.finish()
# Handlers Administrativos
class LoginDevHandler(tornado.web.RequestHandler):
    def get(self): self.render("painel_dev.html", usuarios=listar_usuarios(), notas=listar_notas_geral(), mensagem=None)

class ForcarNotasHandler(tornado.web.RequestHandler):
    def post(self):
        uid = self.get_argument("id")
        ok, msg = forcar_notas_teste(uid)
        if ok:
            self.write({"sucesso": True, "mensagem": "🚀 FULL 10 APLICADO!"})
        else:
            self.write({"sucesso": False, "mensagem": msg or "Erro desconhecido ao aplicar FULL 10"})

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


class CheckFinalStatusHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    def get(self):
        user_id = self.get_current_user()
        if not user_id:
            self.set_status(401); self.write({"can_access": False}); return

        try:
            conn = conectar(); c = conn.cursor()
            # verifica nota_final ou maior nota por modulo
            try:
                c.execute("SELECT nota_final, certificado_fin FROM users WHERE id = ?", (user_id,))
                row = c.fetchone()
                if row and row.get('certificado_fin') == 1:
                    conn.close(); self.write({"can_access": True}); return
                if row and row.get('nota_final') and int(row['nota_final']) >= 6:
                    conn.close(); self.write({"can_access": True}); return
            except Exception:
                pass

            # fallback: checar provas_resultado maiores notas por modulo
            c.execute("SELECT modulo, MAX(nota) as maior_nota FROM provas_resultado WHERE user_id = ? GROUP BY modulo", (user_id,))
            rows = c.fetchall()
            resultados = {r['modulo']: r['maior_nota'] for r in rows}
            required = [1,2,3,4,5]
            aprovado = all(resultados.get(m, 0) >= 6 for m in required)
            conn.close()
            self.write({"can_access": bool(aprovado)})
        except Exception as e:
            try: conn.close()
            except: pass
            self.set_status(500); self.write({"can_access": False, "error": str(e)})

def criar_tabela(): pass
def criar_usuario_admin_se_nao_existe(): pass
def criar_tabela():
    """
    Inicializa as tabelas adicionais necessárias para o sistema.
    Chama o gerador de tabelas de segurança (certificados, auditoria, ips_bloqueados).
    """
    try:
        from app.utils.certificado_security import criar_tabelas_seguranca
        criar_tabelas_seguranca()
    except Exception as e:
        print(f"Erro ao criar tabelas de segurança: {e}")
    try:
        from app.utils.recuperacao_utils import criar_tabelas_recuperacao
        criar_tabelas_recuperacao()
    except Exception as e:
        print(f"Erro ao criar tabelas de segurança: {e}")
    # MIGRAÇÃO SIMPLES: adiciona coluna nota_final se não existir (compatibilidade entre esquemas)
    try:
        conn = conectar(); c = conn.cursor()
        c.execute("PRAGMA table_info(users)")
        cols = [r['name'] for r in c.fetchall()]
        if 'nota_final' not in cols:
            try:
                c.execute("ALTER TABLE users ADD COLUMN nota_final INTEGER")
                conn.commit()
                print('Coluna nota_final adicionada à tabela users')
            except Exception as e:
                print(f"Falha ao adicionar nota_final: {e}")
        conn.close()
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
    return


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

            