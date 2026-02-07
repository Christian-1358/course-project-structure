import sqlite3
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DB = os.path.join(BASE_DIR, "usuarios.db")

def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def usuario_pagou(user_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT pago FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row and row["pago"] == 1

def marcar_como_pago(user_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        UPDATE users
        SET pago = 1
        WHERE id = ?
    """, (user_id,))
    conn.commit()
    conn.close()
