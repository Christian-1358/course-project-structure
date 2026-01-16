import sqlite3
import os
import hashlib
import tornado.web
import json
import time

# ------------------ DATABASE ------------------
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DB = os.path.join(BASE_DIR, "usuarios.db")

def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ------------------ HASH ------------------
def hash_senha(text: str) -> str:
    """Gera hash MD5 da senha"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# ------------------ TABELAS ------------------
def criar_tabela():
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            ativo INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

def criar_tabela_purchases():
    conn = conectar()
    c = conn.cursor()   
    c.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,   
            user_id INTEGER,
            email TEXT,
            metodo TEXT,
            amount REAL,
            status TEXT,
            created_at INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

# ------------------ USUÁRIOS ------------------
def criar_usuario_admin_se_nao_existe():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username='admin'")
    if c.fetchone() is None:
        senha = hash_senha("123456")
        c.execute(
            "INSERT INTO users (username, password, email, ativo) VALUES (?, ?, ?, 1)",
            ("admin", senha, "admin@painel.com")
        )
        conn.commit()
        print("✔ Usuário admin criado | senha: 123456")
    conn.close()

def criar_usuario(username, senha, email=None):
    conn = conectar()
    c = conn.cursor()
    senha_md5 = hash_senha(senha)
    c.execute(
        "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
        (username, senha_md5, email)
    )
    conn.commit()
    conn.close()

def listar_usuarios():
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        SELECT id, username, password, email, ativo
        FROM users
        ORDER BY id
    """)
    usuarios = [dict(row) for row in c.fetchall()]
    conn.close()
    return usuarios

def alterar_status_usuario(user_id, ativo):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not c.fetchone():
        conn.close()
        return False, "Usuário não encontrado"
    c.execute("UPDATE users SET ativo=? WHERE id=?", (ativo, user_id))
    conn.commit()
    conn.close()
    return True, "Usuário bloqueado" if ativo == 0 else "Usuário ativado"

def deletar_usuario(user_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not c.fetchone():
        conn.close()
        return False, "Usuário não encontrado"
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return True, "Usuário deletado com sucesso"

def alterar_senha(user_id, nova_senha):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not c.fetchone():
        conn.close()
        return False, "Usuário não encontrado"
    senha_hash = hash_senha(nova_senha)
    c.execute("UPDATE users SET password=? WHERE id=?", (senha_hash, user_id))
    conn.commit()
    conn.close()
    return True, "Senha alterada com sucesso"

def resetar_senha(user_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not c.fetchone():
        conn.close()
        return False, "Usuário não encontrado"
    senha_padrao = hash_senha("123456")
    c.execute("UPDATE users SET password=? WHERE id=?", (senha_padrao, user_id))
    conn.commit()
    conn.close()
    return True, "Senha resetada para 123456"

def buscar_usuario(filtro):
    conn = conectar()
    c = conn.cursor()
    filtro = f"%{filtro}%"
    c.execute("""
        SELECT id, username, email, ativo
        FROM users
        WHERE username LIKE ? OR email LIKE ?
        ORDER BY id
    """, (filtro, filtro))
    usuarios = [dict(row) for row in c.fetchall()]
    conn.close()
    return usuarios

def autenticar_usuario(username, senha):
    """Retorna dados do usuário se login válido"""
    conn = conectar()
    c = conn.cursor()
    senha_md5 = hash_senha(senha)
    c.execute("""
        SELECT id, username, email, ativo
        FROM users
        WHERE username=? AND password=? AND ativo=1
    """, (username, senha_md5))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

# ------------------ COMPRAS ------------------
def registrar_compra(email, user_id=None, metodo=None, amount=29.99, status="approved"):
    try:
        conn = conectar()
        c = conn.cursor()
        ts = int(time.time())
        c.execute("""
            INSERT INTO purchases (user_id, email, metodo, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, email, metodo, amount, status, ts))
        conn.commit()
        pid = c.lastrowid
        conn.close()
        return True, pid
    except Exception as e:
        return False, str(e)

def contar_compradores(apenas_confirmados=True):
    conn = conectar()
    c = conn.cursor()
    if apenas_confirmados:
        c.execute("SELECT COUNT(DISTINCT email) AS cnt FROM purchases WHERE status='approved' AND email IS NOT NULL")
    else:
        c.execute("SELECT COUNT(DISTINCT email) AS cnt FROM purchases WHERE email IS NOT NULL")
    row = c.fetchone()
    conn.close()
    return int(row["cnt"]) if row and row["cnt"] is not None else 0

def listar_compradores(apenas_confirmados=True):
    conn = conectar()
    c = conn.cursor()
    if apenas_confirmados:
        c.execute("SELECT id, user_id, email, metodo, amount, status, created_at FROM purchases WHERE status='approved' ORDER BY created_at DESC")
    else:
        c.execute("SELECT id, user_id, email, metodo, amount, status, created_at FROM purchases ORDER BY created_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

# ------------------ HANDLERS TORNADO ------------------
class LoginDevHandler(tornado.web.RequestHandler):
    def get(self):
        usuarios = listar_usuarios()
        self.render(
            "painel_dev.html",
            usuarios=usuarios,
            mensagem=None,
            erro=None
        )

class AlterarStatusHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            user_id = int(self.get_argument("id"))
            ativo = int(self.get_argument("ativo"))
        except:
            self.set_status(400)
            return self.write(json.dumps({"sucesso": False, "mensagem": "Parâmetros inválidos"}))
        sucesso, msg = alterar_status_usuario(user_id, ativo)
        self.write(json.dumps({"sucesso": sucesso, "mensagem": msg}))

class AlterarSenhaHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            user_id = int(self.get_argument("id"))
            senha = self.get_argument("senha")
        except:
            self.set_status(400)
            return self.write(json.dumps({"sucesso": False, "mensagem": "Parâmetros inválidos"}))
        sucesso, msg = alterar_senha(user_id, senha)
        self.write(json.dumps({"sucesso": sucesso, "mensagem": msg}))

class ResetarSenhaHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            user_id = int(self.get_argument("id"))
        except:
            self.set_status(400)
            return self.write(json.dumps({"sucesso": False, "mensagem": "ID inválido"}))
        sucesso, msg = resetar_senha(user_id)
        self.write(json.dumps({"sucesso": sucesso, "mensagem": msg}))

class DeletarUsuarioHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            user_id = int(self.get_argument("id"))
        except:
            self.set_status(400)
            return self.write(json.dumps({"sucesso": False, "mensagem": "ID inválido"}))
        sucesso, msg = deletar_usuario(user_id)
        self.write(json.dumps({"sucesso": sucesso, "mensagem": msg}))

class BuscarUsuarioHandler(tornado.web.RequestHandler):
    def get(self):
        filtro = self.get_argument("filtro", "")
        usuarios = buscar_usuario(filtro)
        self.render(
            "painel_dev.html",
            usuarios=usuarios,
            mensagem=None,
            erro=None
        )

class ComprasHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            criar_tabela_purchases()
            compras = listar_compradores(apenas_confirmados=False)
            total = len(compras)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"count": total, "purchases": compras}))
        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({"sucesso": False, "mensagem": str(e)}))
