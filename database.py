import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "usuarios.db")

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def marcar_como_pago(user_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        UPDATE users
        SET pago = 1,
            inicio_curso = datetime('now')
        WHERE id = ?
    """, (user_id,))
    conn.commit()
    conn.close()

def usuario_pagou(user_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT pago FROM users WHERE id = ?", (user_id,))
    r = c.fetchone()
    conn.close()
    return r and r["pago"] == 1
