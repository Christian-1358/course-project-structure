import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")


# ===============================
# CONEXÃO
# ===============================
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
    # USERS
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

        ultimo_modulo INTEGER DEFAULT 1,
        ultima_aula INTEGER DEFAULT 1,
        tempo_total INTEGER DEFAULT 0,

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
        tempo_assistido INTEGER DEFAULT 0,
        data_conclusao TEXT,
        UNIQUE(user_id, modulo, aula),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Índices para performance
    c.execute("CREATE INDEX IF NOT EXISTS idx_progresso_user ON progresso(user_id);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_provas_user ON provas_resultado(user_id);")

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

    conn.commit()
    conn.close()


# ===============================
# PROGRESSO
# ===============================
def salvar_progresso(user_id, modulo, aula, concluida=0, tempo=0):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    INSERT INTO progresso (user_id, modulo, aula, concluida, tempo_assistido, data_conclusao)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id, modulo, aula)
    DO UPDATE SET
        concluida = excluded.concluida,
        tempo_assistido = tempo_assistido + excluded.tempo_assistido,
        data_conclusao = CASE WHEN excluded.concluida = 1 THEN excluded.data_conclusao ELSE data_conclusao END
    """, (
        user_id,
        modulo,
        aula,
        concluida,
        tempo,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S") if concluida else None
    ))

    conn.commit()
    conn.close()


def buscar_progresso(user_id):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT modulo, aula, concluida
        FROM progresso
        WHERE user_id = ?
    """, (user_id,))

    rows = c.fetchall()
    conn.close()

    return [
        {"modulo": r["modulo"], "aula": r["aula"], "concluida": r["concluida"]}
        for r in rows
    ]


def calcular_percentual(user_id):
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as total FROM progresso WHERE user_id = ?", (user_id,))
    total = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) as concluidas FROM progresso WHERE user_id = ? AND concluida = 1", (user_id,))
    concluidas = c.fetchone()["concluidas"]

    conn.close()

    if total == 0:
        return 0

    return round((concluidas / total) * 100)


# ===============================
# PAGAMENTO
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

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
        UPDATE users
        SET pago = 1,
            data_pagamento = ?,
            inicio_curso = ?
        WHERE id = ?
    """, (agora, agora, user_id))

    conn.commit()
    conn.close()


# ===============================
# CERTIFICADO FINAL
# ===============================
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


def pode_fazer_prova_final(user_id):
    percentual = calcular_percentual(user_id)
    return percentual >= 100


# ===============================
# EXECUÇÃO DIRETA
# ===============================
if __name__ == "__main__":
    print("-" * 60)
    criar_banco()
    print("🚀 BANCO CRIADO / ATUALIZADO COM SUCESSO")
    print("📁 Banco:", DB_PATH)
    print("-" * 60)
