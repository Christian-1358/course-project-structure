import sqlite3
import os
from datetime import datetime

# ===============================
# CONFIGURAÇÃO DO BANCO
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")


def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ===============================
# CRIAÇÃO / MIGRAÇÃO DO BANCO
# ===============================
def criar_banco():
    conn = conectar()
    c = conn.cursor()

    c.execute("PRAGMA foreign_keys = ON;")

    # ===============================
    # TABELA USERS
    # ===============================
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        nome TEXT,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        ativo INTEGER DEFAULT 1,

        pago INTEGER DEFAULT 0,
        data_pagamento TEXT,

        created_at TEXT,
        inicio_curso TEXT,

        fim_modulo1 TEXT,
        fim_modulo2 TEXT,
        fim_modulo3 TEXT,
        fim_modulo4 TEXT,
        fim_modulo5 TEXT,

        certificado_fin INTEGER DEFAULT 0
    );
    """)

    # ===============================
    # PROVAS
    # ===============================
    c.execute("""
    CREATE TABLE IF NOT EXISTS provas_resultado (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        modulo INTEGER NOT NULL,
        nota REAL NOT NULL,
        aprovado INTEGER NOT NULL,
        data TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # ===============================
    # PROGRESSO
    # ===============================
    c.execute("""
    CREATE TABLE IF NOT EXISTS progresso (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        modulo INTEGER NOT NULL,
        aula INTEGER NOT NULL,
        concluida INTEGER DEFAULT 0,
        UNIQUE(user_id, modulo, aula),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # ===============================
    # RECUPERAÇÃO DE SENHA
    # ===============================
    c.execute("""
    CREATE TABLE IF NOT EXISTS password_reset (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        expires_at TEXT NOT NULL,
        last_request TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # ===============================
    # MIGRAÇÃO SEGURA DE COLUNAS
    # ===============================
    colunas = [
        ("nome", "TEXT"),
        ("created_at", "TEXT"),
        ("inicio_curso", "TEXT"),
        ("pago", "INTEGER DEFAULT 0"),
        ("data_pagamento", "TEXT"),
        ("certificado_fin", "INTEGER DEFAULT 0"),
    ]

    for coluna, tipo in colunas:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {coluna} {tipo}")
        except sqlite3.OperationalError:
            pass

    # ===============================
    # BACKFILL
    # ===============================
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
        UPDATE users
        SET created_at = ?
        WHERE created_at IS NULL
    """, (agora,))

    conn.commit()
    conn.close()


# ===============================
# FUNÇÕES DE NEGÓCIO
# ===============================
def usuario_pagou(user_id):
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT pago FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()

    conn.close()
    return bool(row and row["pago"] == 1)


def liberar_pagamento(user_id):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
        UPDATE users
        SET pago = 1,
            data_pagamento = ?,
            inicio_curso = ?
        WHERE id = ?
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        user_id
    ))

    conn.commit()
    conn.close()
    print(f"💳 Pagamento liberado | user_id={user_id}")


def liberar_certificado_final(user_id):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
        UPDATE users
        SET certificado_fin = 1
        WHERE id = ?
    """, (user_id,))

    conn.commit()
    conn.close()
    print(f"🏆 Certificado FINAL liberado | user_id={user_id}")


# ===============================
# EXECUÇÃO DIRETA
# ===============================
if __name__ == "__main__":
    print("-" * 60)
    criar_banco()
    print("🚀 BANCO CRIADO / ATUALIZADO COM SUCESSO")
    print("📁 Banco:", DB_PATH)
    print("-" * 60)
