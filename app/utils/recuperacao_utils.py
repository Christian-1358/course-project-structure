import os
import sqlite3
from datetime import datetime, timedelta

from app.utils.admin_tools import conectar


def criar_tabelas_recuperacao():
    conn = conectar()
    c = conn.cursor()
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS recuperacao_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                modulo INTEGER NOT NULL,
                attempts INTEGER DEFAULT 0,
                last_attempt TEXT,
                lock_until TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def get_attempt(user_id, modulo):
    conn = conectar(); c = conn.cursor()
    c.execute("SELECT id, attempts, last_attempt, lock_until FROM recuperacao_attempts WHERE user_id = ? AND modulo = ? LIMIT 1", (user_id, modulo))
    row = c.fetchone(); conn.close()
    return dict(row) if row else None


def increment_attempt(user_id, modulo, threshold=2, lock_hours=24):
    now = datetime.now()
    row = get_attempt(user_id, modulo)
    conn = conectar(); c = conn.cursor()

    if row:
        # check lock
        lock_until = row.get('lock_until')
        if lock_until:
            try:
                lock_dt = datetime.fromisoformat(lock_until)
                if lock_dt > now:
                    conn.close()
                    return {'locked': True, 'lock_until': lock_until}
            except Exception:
                pass

        attempts = row['attempts'] + 1
        if attempts > threshold:
            lock_dt = now + timedelta(hours=lock_hours)
            c.execute("UPDATE recuperacao_attempts SET attempts = 0, last_attempt = ?, lock_until = ? WHERE id = ?", (now.isoformat(), lock_dt.isoformat(), row['id']))
            conn.commit(); conn.close()
            return {'locked': True, 'lock_until': lock_dt.isoformat()}
        else:
            c.execute("UPDATE recuperacao_attempts SET attempts = ?, last_attempt = ? WHERE id = ?", (attempts, now.isoformat(), row['id']))
            conn.commit(); conn.close()
            return {'locked': False, 'attempts': attempts}

    else:
        # create record
        c.execute("INSERT INTO recuperacao_attempts (user_id, modulo, attempts, last_attempt) VALUES (?, ?, 1, ?)", (user_id, modulo, now.isoformat()))
        conn.commit(); conn.close()
        return {'locked': False, 'attempts': 1}


def reset_attempts(user_id, modulo):
    conn = conectar(); c = conn.cursor()
    c.execute("DELETE FROM recuperacao_attempts WHERE user_id = ? AND modulo = ?", (user_id, modulo))
    conn.commit(); conn.close()
