# server.py
import os
import sqlite3
import json
import uuid
from datetime import datetime
import tornado.ioloop
import tornado.web

# ===============================
# CONFIGURAÇÃO DE BANCO
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "checkout.db")

def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        created_at TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_name TEXT,
        amount REAL,
        payment_method TEXT,
        status TEXT,
        created_at TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        payment_code TEXT,
        status TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

criar_tabelas()

# ===============================
# HANDLERS
# ===============================
class BaseHandler(tornado.web.RequestHandler):
    def write_json(self, data):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data))

class CheckoutHandler(BaseHandler):
    async def post(self, method):
        """
        Recebe o tipo de pagamento: pix, card, paypal, boleto
        e processa simuladamente
        """
        data = json.loads(self.request.body.decode())
        product = data.get("product_name", "Mentoria Mestre das Milhas")
        amount = data.get("amount", 200.00)
        user_id = data.get("user_id", 1)  # por agora fixo
        now = datetime.now().isoformat()

        conn = conectar()
        cursor = conn.cursor()

        # Criar order
        cursor.execute(
            "INSERT INTO orders (user_id, product_name, amount, payment_method, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, product, amount, method, "pending", now)
        )
        order_id = cursor.lastrowid
        conn.commit()

        # Processamento simulado
        if method == "pix":
            code = f"PIX{uuid.uuid4().hex[:20]}"
            status = "waiting"
        elif method == "card":
            code = f"CARD{uuid.uuid4().hex[:20]}"
            status = "paid"
        elif method == "paypal":
            code = f"PAYPAL{uuid.uuid4().hex[:20]}"
            status = "redirect"  # front vai redirecionar
        elif method == "boleto":
            code = f"BOLETO{uuid.uuid4().hex[:20]}"
            status = "waiting"
        else:
            self.set_status(400)
            self.write_json({"error": "Método inválido"})
            return

        # Salvar payment
        cursor.execute(
            "INSERT INTO payments (order_id, payment_code, status, created_at) VALUES (?, ?, ?, ?)",
            (order_id, code, status, now)
        )
        conn.commit()
        conn.close()

        # Retornar dados para o frontend
        self.write_json({
            "order_id": order_id,
            "payment_code": code,
            "status": status
        })

class OrdersHandler(BaseHandler):
    def get(self):
        """
        Retorna todas as orders (para admin/testes)
        """
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders")
        orders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        self.write_json({"orders": orders})

# ===============================
# ROTAS
# ===============================
def make_app():
    return tornado.web.Application([
        (r"/checkout/([a-zA-Z]+)", CheckoutHandler),
        (r"/orders", OrdersHandler),
    ], debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("🚀 Servidor rodando em http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()
