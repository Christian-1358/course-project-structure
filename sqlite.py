import sqlite3
import os

# Configuração de Caminho Profissional
BASE_DIR = os.path.abspath(os.getcwd())
DB = os.path.join(BASE_DIR, "usuarios.db")

def criar_banco():
    # Usando o context manager para garantir que a conexão feche
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON;")

        # ================= TABELA: USERS =================
        # Adicionada a coluna 'nome' (para o certificado) e as colunas de módulos
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            nome TEXT,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            ativo INTEGER DEFAULT 1,
            inicio_curso TEXT,
            fim_modulo1 TEXT,
            fim_modulo2 TEXT,
            fim_modulo3 TEXT,
            fim_modulo4 TEXT,
            fim_modulo5 TEXT
        );
        """)

        # --- MIGRACAO: Garante que colunas novas entrem em bancos antigos ---
        colunas_necessarias = [
            ("nome", "TEXT"),
            ("inicio_curso", "TEXT"),
            ("fim_modulo1", "TEXT"),
            ("fim_modulo2", "TEXT"),
            ("fim_modulo3", "TEXT"),
            ("fim_modulo4", "TEXT"),
            ("fim_modulo5", "TEXT")
        ]

        for nome_col, tipo_col in colunas_necessarias:
            try:
                c.execute(f"ALTER TABLE users ADD COLUMN {nome_col} {tipo_col}")
                print(f"Coluna '{nome_col}' adicionada com sucesso.")
            except sqlite3.OperationalError:
                # Se cair aqui, é porque a coluna já existe
                pass

        # ================= TABELA: PROVAS =================
        c.execute("""
        CREATE TABLE IF NOT EXISTS provas_resultado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            modulo INTEGER NOT NULL,
            nota REAL NOT NULL,
            aprovado INTEGER NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # ================= TABELA: PROGRESSO =================
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

        # ================= TABELA: PASSWORD RESET =================
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

        conn.commit()

if __name__ == "__main__":
    criar_banco()
    print("-" * 30)
    print("🚀 ESTRUTURA ELITE ATUALIZADA")
    print("Local:", DB)
    print("-" * 30)