import sqlite3
import os

# Configuração de Caminho Absoluto
BASE_DIR = os.path.abspath(os.getcwd())
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

def criar_banco():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON;")

        # 1. TABELA PRINCIPAL: USERS
        # Contém dados de acesso, nome para o certificado e datas de conclusão
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

        # 2. MIGRACAO E ATUALIZAÇÃO DE COLUNAS
        # Garante que mesmo que o banco já exista, as novas colunas sejam inseridas
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
                print(f"✅ Coluna '{nome_col}' verificada/adicionada.")
            except sqlite3.OperationalError:
                # Coluna já existe, ignora o erro
                pass

        # 3. TABELA: RESULTADOS DAS PROVAS
        # Onde o sistema consulta se o aluno atingiu a nota para o certificado
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

        # 4. TABELA: PROGRESSO (Aulas Assistidas)
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

        # 5. TABELA: RECUPERAÇÃO DE SENHA
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

# Script para preencher dados de teste e liberar o Certificado 2
def liberar_teste(user_id=1):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Define a data de hoje para o teste
        data_hoje = "30/01/2026"
        c.execute("""
            UPDATE users 
            SET inicio_curso = ?, fim_modulo2 = ? 
            WHERE id = ?
        """, ("01/01/2026", data_hoje, user_id))
        conn.commit()
    print(f"⭐ Certificado Módulo 2 liberado para o usuário ID {user_id}")

if __name__ == "__main__":
    print("-" * 40)
    criar_banco()
    # Descomente a linha abaixo se quiser liberar o certificado 2 manualmente para testar
    # liberar_teste(1)
    print("🚀 ESTRUTURA MILHASPRO ATUALIZADA COM SUCESSO")
    print("Arquivo:", DB_PATH)
    print("-" * 40)