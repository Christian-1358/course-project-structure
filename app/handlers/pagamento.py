#bom, me ajude a criar um comando que ira ver se o ususario pagou o curso, se ele pagou, ele pode acessar o curso, se não, ele é redirecionado para a página de pagamento. O comando deve ser colocado no início de cada handler que precisa dessa verificação. O comando deve ser algo como:


import os
import sqlite3
import json
import uuid
from datetime import datetime
import tornado.ioloop
import tornado.web
from app.utils.pagamento_utils import usuario_pagou, marcar_como_pago

# MercadoPago token (use sandbox access token). Set via env var `MP_ACCESS_TOKEN`.
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")
mp_client = None

# Tentar importar e inicializar MercadoPago se disponível
try:
    import mercadopago
    if MP_ACCESS_TOKEN:
        mp_client = mercadopago.SDK(MP_ACCESS_TOKEN)
except ImportError:
    print("[pagamento] mercadopago SDK não instalado. Use fallback de pagamento manual.")
except Exception as e:
    print(f"[pagamento] erro ao inicializar MercadoPago: {e}")

# ===============================
# CONFIGURAÇÃO DE BANCO
# ===============================

class PagamentoPageHandler(tornado.web.RequestHandler):
    def get(self):
        # Tenta obter user_id do cookie ou querystring
        user_id = None
        cookie = self.get_secure_cookie("user_id")
        if cookie:
            try:
                user_id = int(cookie.decode() if isinstance(cookie, bytes) else cookie)
            except Exception:
                user_id = None

        if not user_id:
            q = self.get_argument("user_id", None)
            if q:
                try:
                    user_id = int(q)
                except Exception:
                    user_id = None

        # Se usuário já pagou, libera acesso (redireciona para o curso)
        if user_id and usuario_pagou(user_id):
            self.redirect("/login   ")
            return

        # Caso contrário, mostra a página de pagamento com mensagem de erro
        self.set_status(402)
        self.write("""
        <html>
          <head><title>Pagamento obrigatório</title></head>
          <body style="font-family:Arial, Helvetica, sans-serif; text-align:center; padding:40px;">
            <h1>Erro: acesso não liberado</h1>
            <p>O usuário não efetuou o pagamento do curso. Por favor, realize o pagamento para liberar sua conta.</p>
            <a href="/pagamento">Ir para página de pagamento</a>
          </body>
        </html>
        """)

    def post(self):
        # Endpoint simples para marcar pagamento (usado após confirmação)
        # Aceita JSON ou form com `user_id`.
        try:
            user_id = None
            cookie = self.get_secure_cookie("user_id")
            if cookie:
                try:
                    user_id = int(cookie.decode() if isinstance(cookie, bytes) else cookie)
                except Exception:
                    user_id = None

            if not user_id:
                user_id = self.get_argument("user_id", None)
                if user_id:
                    user_id = int(user_id)

            if not user_id:
                self.set_status(400)
                self.write("<h1>Erro: user_id não informado</h1>")
                return

            # Marca como pago
            marcar_como_pago(user_id)

            # Resposta HTML simples informando sucesso
            self.write("""
            <html>
              <head><title>Pagamento confirmado</title></head>
              <body style="font-family:Arial, Helvetica, sans-serif; text-align:center; padding:40px;">
                <h1>Pagamento confirmado</h1>
                <p>Pagamento registrado com sucesso. Seu acesso foi liberado.</p>
                <a href="/curso">Ir para o curso</a>
              </body>
            </html>
            """)
        except Exception as e:
            self.set_status(500)
            self.write(f"<h1>Erro interno</h1><pre>{e}</pre>")


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
    
    def get(self):
        # Renderiza a página de pagamento (rota /pagamento)
        try:
            # tenta passar user_id para o template (para criar preferência ligada ao usuário)
            user_id = None
            cookie = self.get_secure_cookie("user_id")
            if cookie:
                try:
                    user_id = int(cookie.decode() if isinstance(cookie, bytes) else cookie)
                except Exception:
                    user_id = None
            self.render("pagamento.html", user_id=user_id, amount=200.0)
        except Exception:
            # Fallback simples se o template não existir
            self.set_status(200)
            self.write("<h1>Página de pagamento</h1><p>Implemente o front-end de pagamento.</p>")


class MercadoPagoCreateHandler(BaseHandler):
    async def post(self):
        """
        Cria uma preferência de pagamento no MercadoPago.
        Se SDK não estiver configurado, retorna um placeholder.
        """
        if not mp_client:
            # Fallback: retorna uma resposta que permite uso manual ou dev
            self.set_status(503)
            return self.write_json({
                "error": "MercadoPago não configurado",
                "hint": "Configure MP_ACCESS_TOKEN e instale o SDK para usar pagamento real",
                "fallback": "Use os endpoints de admin para marcar pagamento manualmente"
            })

        try:
            data = json.loads(self.request.body.decode())
        except Exception:
            data = {k: self.get_argument(k) for k in self.request.arguments}

        user_id = data.get("user_id")
        amount = float(data.get("amount", 200.0))
        title = data.get("title", "Mentoria Mestre das Milhas")

        preference_data = {
            "items": [
                {
                    "title": title,
                    "quantity": 1,
                    "unit_price": float(amount)
                }
            ],
            "metadata": {"user_id": str(user_id)},
            "back_urls": {
                "success": "http://localhost:8080/pagamentotrue",
                "failure": "http://localhost:8080/pagamento",
                "pending": "http://localhost:8080/pagamento"
            },
            "auto_return": "approved"
        }

        try:
            preference = mp_client.preference().create(preference_data)
            res = preference.get('response', {})
            return self.write_json({"preference": res})
        except Exception as e:
            print(f"[pagamento] erro ao criar preferência: {e}")
            return self.write_json({"error": str(e)})


class MercadoPagoWebhookHandler(tornado.web.RequestHandler):
    def post(self):
        """
        Recebe notificações de pagamento do MercadoPago.
        Se SDK não estiver configurado, apenas confirma o recebimento.
        """
        if not mp_client:
            print("[pagamento] webhook recebido mas MercadoPago não configurado; ignorando")
            self.write("ok")
            return

        try:
            body = json.loads(self.request.body.decode())
        except Exception:
            body = self.request.arguments

        payment_id = None
        # notification style: {"type":"payment","data":{"id":12345}}
        if isinstance(body, dict):
            if "data" in body and isinstance(body["data"], dict):
                payment_id = body["data"].get("id")
            elif "id" in body:
                payment_id = body.get("id")

        if not payment_id and self.get_argument("id", None):
            payment_id = self.get_argument("id")

        if not payment_id:
            self.set_status(400)
            self.write("ok")
            return

        try:
            payment = mp_client.payment().get(payment_id)
            payment_resp = payment.get('response', {})
            status = payment_resp.get('status')
            metadata = payment_resp.get('metadata', {})
            user_id = metadata.get('user_id')

            if status == 'approved' and user_id:
                try:
                    marcar_como_pago(int(user_id))
                    print(f"[pagamento] pagamento aprovado user_id={user_id}")
                except Exception as e:
                    print(f"[pagamento] erro ao marcar como pago: {e}")

        except Exception as e:
            print(f"[pagamento] erro webhook: {e}")

        self.write("ok")

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

