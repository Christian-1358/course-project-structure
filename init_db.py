import sqlite3
import os

DB = "usuarios.db"

conn = sqlite3.connect(DB)
c = conn.cursor()

# ===============================
# TABELA DE USUÁRIOS
# ===============================
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE,
    ativo INTEGER DEFAULT 1,

    inicio_curso TEXT,

    fim_modulo1 TEXT,
    fim_modulo2 TEXT,
    fim_modulo3 TEXT,
    fim_modulo4 TEXT,
    fim_modulo5 TEXT,

    modulo_1 INTEGER DEFAULT 0,
    modulo_2 INTEGER DEFAULT 0,
    modulo_3 INTEGER DEFAULT 0,
    modulo_4 INTEGER DEFAULT 0,
    modulo_5 INTEGER DEFAULT 0,

    nota_final INTEGER,
    certificado_mestre TEXT
);
""")


# ===============================
# USUÁRIO ADMIN PADRÃO
# ===============================
import hashlib

def hash_senha(text):
    return hashlib.sha256(text.encode()).hexdigest()

c.execute("""
SELECT id FROM users WHERE username = 'admin'
""")

if not c.fetchone():
    c.execute("""
    INSERT INTO users (username, password, email, ativo, inicio_curso)
    VALUES (?, ?, ?, 1, NULL)
    """, (
        "admin",
        hash_senha("admin123"),
        "admin@admin.com"
    ))
    print("Usuário admin criado")

conn.commit()
conn.close()

print("Banco de dados criado e verificado com sucesso.")

