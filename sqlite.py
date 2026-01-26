import sqlite3
import os
import datetime

BASE_DIR = os.path.abspath(os.getcwd())
DB = os.path.join(BASE_DIR, "usuarios.db")

def criar_banco():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()

        c.execute("PRAGMA foreign_keys = ON;")

        # ================= USERS =================
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            ativo INTEGER DEFAULT 1
        );
        """)
    c.execute("""
CREATE TABLE IF NOT EXISTS provas_resultado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    modulo INTEGER NOT NULL,
    nota REAL NOT NULL,
    aprovado INTEGER NOT NULL,
    data TEXT NOT NULL
)
""")

        # ================= PROGRESSO =================
    c.execute("""
        CREATE TABLE IF NOT EXISTS progresso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            modulo INTEGER NOT NULL,
            aula INTEGER NOT NULL,
            concluida INTEGER DEFAULT 0,
            UNIQUE(user_id, modulo, aula),
            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
        """)

        # ================= PASSWORD RESET =================
    c.execute("""
        CREATE TABLE IF NOT EXISTS password_reset (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            last_request TEXT NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
        """)

    conn.commit()

if __name__ == "__main__":
    criar_banco()
    print("Banco criado/atualizado com sucesso em:", DB)
