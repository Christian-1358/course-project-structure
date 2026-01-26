import sqlite3

conn = sqlite3.connect("curso.db")
c = conn.cursor()

# USUÁRIOS
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    ativo INTEGER DEFAULT 1,
    inicio_curso TEXT,
    fim_modulo1 TEXT
)
""")

# PROVAS
c.execute("""
CREATE TABLE IF NOT EXISTS provas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    modulo INTEGER NOT NULL,
    nota REAL NOT NULL,
    aprovado INTEGER NOT NULL,
    data_prova TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("Banco criado com sucesso.")
