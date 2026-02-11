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
    try:
        conn = conectar()
        c = conn.cursor()
        c.execute("SELECT pago FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        conn.close()

        pago_val = None
        if row is None:
            print(f"[pagamento_utils] usuario_pagou: user_id={user_id} -> user not found")
            return False

        try:
            pago_val = int(row["pago"])
        except Exception:
            pago_val = row["pago"]

        result = pago_val == 1
        print(f"[pagamento_utils] usuario_pagou: user_id={user_id} -> pago={pago_val} -> {result}")
        return result
    except Exception as e:
        print(f"[pagamento_utils] erro ao checar usuario_pagou user_id={user_id}: {e}")
        return False
    
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
