fazer o pagamento


import tornado.web
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DB = os.path.join(BASE_DIR, "usuarios.db")


def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


class PagamentoPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("pagamento.html")


class ConfirmarPagamentoHandler(tornado.web.RequestHandler):
    def post(self):
        user_id = self.get_secure_cookie("user_id")

        if not user_id:
            self.redirect("/login")
            return

        user_id = int(user_id.decode())

        conn = conectar()
        c = conn.cursor()

        c.execute("""
            UPDATE users
            SET pago = 1,
                data_pagamento = ?
            WHERE id = ?
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))

        conn.commit()
        conn.close()

        self.redirect("/curso")
