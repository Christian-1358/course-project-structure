import sqlite3
import os
from datetime import datetime

# ===============================
# CONFIGURAÇÃO DO BANCO
# ===============================
BASE_DIR = os.path.abspath(os.getcwd())
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

# ===============================
# CRIAÇÃO / ATUALIZAÇÃO DO BANCO
# ===============================
def criar_banco():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON;")

        # ==================================================
        # TABELA USERS
        # ==================================================
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            nome TEXT,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            ativo INTEGER DEFAULT 1,

            pago INTEGER DEFAULT 0,

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

        # ==================================================
        # TABELA RESULTADO DAS PROVAS
        # ==================================================
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

        # ==================================================
        # TABELA PROGRESSO
        # ==================================================
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

        # ==================================================
        # TABELA RECUPERAÇÃO DE SENHA
        # ==================================================
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

        # ==================================================
        # MIGRAÇÃO DE COLUNAS (SAFE)
        # ==================================================
        colunas_necessarias = [
            ("nome", "TEXT"),
            ("created_at", "TEXT"),
            ("inicio_curso", "TEXT"),
            ("fim_modulo1", "TEXT"),
            ("fim_modulo2", "TEXT"),
            ("fim_modulo3", "TEXT"),
            ("fim_modulo4", "TEXT"),
            ("fim_modulo5", "TEXT"),
            ("pago", "INTEGER DEFAULT 0"),
            ("certificado_fin", "INTEGER DEFAULT 0"),
        ]

        for nome_col, tipo_col in colunas_necessarias:
            try:
                c.execute(f"ALTER TABLE users ADD COLUMN {nome_col} {tipo_col}")
            except sqlite3.OperationalError:
                pass

        # ==================================================
        # BACKFILL DE DADOS
        # ==================================================
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute("""
            UPDATE users
            SET created_at = ?
            WHERE created_at IS NULL
        """, (agora,))

        conn.commit()

# ===============================
# FUNÇÕES AUXILIARES (ADMIN / TESTE)
# ===============================
def liberar_certificado_final(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE users
            SET certificado_fin = 1
            WHERE id = ?
        """, (user_id,))
        conn.commit()

    print(f"🏆 Certificado FINAL liberado | user_id={user_id}")

def liberar_pagamento(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE users
            SET pago = 1,
                inicio_curso = ?
            WHERE id = ?
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
        conn.commit()

    print(f"💳 Pagamento liberado | user_id={user_id}")

# ===============================
# EXECUÇÃO DIRETA
# ===============================
if __name__ == "__main__":
    print("-" * 60)
    criar_banco()
    print("🚀 BANCO ATUALIZADO COM SUCESSO")
    print("📁 Arquivo:", DB_PATH)
    print("-" * 60)
