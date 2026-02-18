import os
import sqlite3
import json
import uuid
from datetime import datetime
import tornado.ioloop
import tornado.web

from app.utils.pagamento_utils import usuario_pagou, marcar_como_pago
from app.handlers.base import BaseHandler

# ===============================
# CREDENCIAIS MERCADOPAGO
# ===============================
# por padrão usamos as chaves de sandbox (ambiente de testes) que já
# estão configuradas aqui para simplificar o desenvolvimento. em
# produção você deve sobrescrever essas variáveis via ambiente
# (ou outro mecanismo de configuração) com as chaves reais.
MP_PUBLIC_KEY = os.environ.get(
    "MP_PUBLIC_KEY",
    "APP_USR-19b62fa6-1ef6-4489-a96f-35bd1bdc46fe"  # sandbox
)
MP_ACCESS_TOKEN = os.environ.get(
    "MP_ACCESS_TOKEN",
    "APP_USR-2389431682625478-021615-6fbe7fc838c104cb7b16f23f966ba6da-3207195955"  # sandbox
)

mp_client = None
# Tentar importar e inicializar MercadoPago se disponível
try:
    import mercadopago
    if MP_ACCESS_TOKEN:
        mp_client = mercadopago.SDK(MP_ACCESS_TOKEN)
        print("[pagamento] MercadoPago SDK inicializado com sucesso!")
except ImportError:
    print("[pagamento]   mercadopago SDK não instalado. Instale com: pip install mercado-pago")
except Exception as e:
    print(f"[pagamento]  erro ao inicializar MercadoPago: {e}")

# ===============================
# CONFIGURAÇÃO DE BANCO
# ===============================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# o diretório raiz do projeto (um nível acima de app)
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DB_USUARIOS = os.path.join(PROJECT_ROOT, "usuarios.db")
DB_CHECKOUT = os.path.join(PROJECT_ROOT, "checkout.db")

def conectar_usuarios():
    """Conecta ao banco de dados de usuários"""
    conn = sqlite3.connect(DB_USUARIOS)
    conn.row_factory = sqlite3.Row
    return conn

def conectar_checkout():
    """Conecta ao banco de dados de checkout/pedidos"""
    conn = sqlite3.connect(DB_CHECKOUT)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas_checkout():
    """Cria as tabelas de checkout se não existirem"""
    conn = conectar_checkout()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_name TEXT,
        amount REAL,
        payment_method TEXT,
        status TEXT,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        payment_code TEXT,
        payment_id TEXT,
        status TEXT,
        created_at TEXT,
        FOREIGN KEY(order_id) REFERENCES orders(id)
    )
    """)
    
    conn.commit()
    conn.close()

# Inicializar tabelas
criar_tabelas_checkout()

# ===============================
# HANDLERS DE PAGAMENTO
# ===============================

class PagamentoPageHandler(BaseHandler):
    """
    Handler para renderizar a página de pagamento.
    Verifica se o usuário já pagou e redireciona para o curso se sim.
    """
    
    def write_json(self, data):
        """Helper para escrever JSON"""
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data))
    
    def get(self):
        """
        Renderiza a página de pagamento.
        Se o usuário já pagou, redireciona para o curso.
        """
        # Obtém user_id do cookie
        user_id = self.get_current_user()
        
        if user_id and usuario_pagou(user_id):
            # Usuário já pagou, libera acesso
            self.redirect("/curso")
            return
        
        # Renderiza a página de pagamento
        try:
            mp_available = mp_client is not None
            self.render(
                "pagamento.html",
                user_id=user_id,
                amount=200.0,
                mp_available=mp_available,
                mp_public_key=MP_PUBLIC_KEY
            )
        except Exception as e:
            print(f"[pagamento] erro ao renderizar template: {e}")
            self.set_status(200)
            self.write("""
            <html>
              <head><title>Pagamento</title></head>
              <body style="font-family:Arial, sans-serif; text-align:center; padding:40px;">
                <h1>Página de Pagamento</h1>
                <p>Mentoria Mestre das Milhas - R$ 200,00</p>
                <p>Aguarde o carregamento da página...</p>
              </body>
            </html>
            """)


class MercadoPagoCreateHandler(BaseHandler):
    """
    Handler para criar preferência de pagamento no MercadoPago.
    Endpoint: POST /pagamento/criar
    """
    
    def write_json(self, data):
        """Helper para escrever JSON"""
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data))
    
    async def post(self):
        """
        Cria uma preferência de pagamento no MercadoPago.
        Espera JSON:
        {
            "user_id": 123,
            "amount": 200.0,
            "title": "Mentoria Mestre das Milhas",
            "method": "pix" | "card" | "paypal" | "boleto"
        }
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
            return self.write_json({"error": "JSON inválido"})

        user_id = data.get("user_id")
        amount = float(data.get("amount", 200.0))
        title = data.get("title", "Mentoria Mestre das Milhas")
        method = data.get("method", "pix")

        if not user_id:
            return self.write_json({"error": "user_id é obrigatório"})

        # tokens enviados pelo frontend (SDK JS) são usados para pagamentos
        # diretos no cartão, sem redirecionamento. caso contrário criamos
        # uma preferência que envia o cliente para a página do MP.
        card_token = data.get("card_token")
        installments = int(data.get("installments", 1))
        payer_email = data.get("payer_email", "" )

        if method == "card" and card_token:
            # pagamento direto com token
            try:
                payment_data = {
                    "transaction_amount": amount,
                    "token": card_token,
                    "description": title,
                    "installments": installments,
                    "payment_method_id": "credit_card",
                    "payer": {"email": payer_email or "test_user@example.com"}
                }
                payment = mp_client.payment().create(payment_data)
                resp = payment.get('response', {})
                print(f"[pagamento] pagamento direto criado: {resp}")

                # se aprovado, marcamos o usuário
                if resp.get('status') == 'approved':
                    try:
                        marcar_como_pago(int(user_id))
                    except Exception as e:
                        print(f"[pagamento] erro ao marcar como pago: {e}")

                return self.write_json({"payment": resp})
            except Exception as e:
                print(f"[pagamento] erro ao processar pagamento direto: {e}")
                return self.write_json({"error": str(e)})

        # caso contrário construímos preferência normal
        preference_data = {
            "items": [
                {
                    "title": title,
                    "quantity": 1,
                    "unit_price": float(amount)
                }
            ],
            "metadata": {"user_id": str(user_id), "method": method},
            "back_urls": {
                "success": "http://localhost:8080/curso",
                "failure": "http://localhost:8080/pagamento",
                "pending": "http://localhost:8080/pagamento"
            },
            "auto_return": "approved",
            "notification_url": "http://localhost:8080/pagamento/webhook"
        }

        try:
            if method == 'pix':
                # criar pagamento direto para PIX (não usamos preferência)
                payment_data = {
                    "transaction_amount": float(amount),
                    "description": title,
                    "payment_method_id": "pix",
                    # alguns campos básicos para o pagador
                    "payer": {"id": str(user_id)}
                }
                payment = mp_client.payment().create(payment_data)
                pay_resp = payment.get('response', {})
                print(f"[pagamento] Pagamento PIX criado user_id={user_id}, id={pay_resp.get('id')}")
                return self.write_json({"payment": pay_resp})
            else:
                preference = mp_client.preference().create(preference_data)
                res = preference.get('response', {})

                # determinar url que será usada pelo frontend; em sandbox o SDK
                # retorna também um campo `sandbox_init_point`, então vamos
                # privilegiar esse valor quando estiver presente (chave de teste).
                init_url = res.get('sandbox_init_point') or res.get('init_point')

                # Log da preferência criada
                print(f"[pagamento] Preferência criada para user_id={user_id}, url={init_url}")

                # devolvemos a url já selecionada para simplificar o front
                return self.write_json({"preference": res, "url": init_url})
        except Exception as e:
            print(f"[pagamento] erro ao criar preferência: {e}")
            return self.write_json({"error": str(e)})


class MercadoPagoWebhookHandler(tornado.web.RequestHandler):
    """
    Handler para receber notificações de pagamento do MercadoPago.
    Endpoint: POST /pagamento/webhook
    """
    
    def post(self):
        """
        Recebe notificações de pagamento aprovado.
        Marca o usuário como pago no banco de dados.
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

            print(f"[pagamento] Webhook recebido: payment_id={payment_id}, status={status}, user_id={user_id}")

            if status == 'approved' and user_id:
                try:
                    marcar_como_pago(int(user_id))
                    print(f"[pagamento] ✅ Pagamento aprovado e marcado para user_id={user_id}")
                except Exception as e:
                    print(f"[pagamento] erro ao marcar como pago: {e}")

        except Exception as e:
            print(f"[pagamento] erro webhook: {e}")

        self.write("ok")


class CheckoutHandler(BaseHandler):
    """
    Handler para processar checkout com múltiplos métodos de pagamento.
    Endpoint: POST /checkout/{method}
    Methods: pix, card, paypal, boleto
    """
    
    def write_json(self, data):
        """Helper para escrever JSON"""
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data))
    
    async def post(self, method):
        """
        Processa checkout com o método especificado.
        """
        try:
            data = json.loads(self.request.body.decode())
        except Exception:
            return self.write_json({"error": "JSON inválido"})

        product = data.get("product_name", "Mentoria Mestre das Milhas")
        amount = data.get("amount", 200.00)
        user_id = data.get("user_id")
        now = datetime.now().isoformat()

        if not user_id:
            return self.write_json({"error": "user_id é obrigatório"})

        conn = conectar_checkout()
        cursor = conn.cursor()

        # Criar order
        cursor.execute(
            """INSERT INTO orders 
               (user_id, product_name, amount, payment_method, status, created_at) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, product, amount, method, "pending", now)
        )
        order_id = cursor.lastrowid
        conn.commit()

        # Processamento simulado por método
        if method == "pix":
            code = f"PIX{uuid.uuid4().hex[:20]}"
            status = "waiting"
        elif method == "card":
            code = f"CARD{uuid.uuid4().hex[:20]}"
            status = "paid"
            # Marcar como pago imediatamente para cartão (simulado)
            try:
                marcar_como_pago(int(user_id))
            except Exception as e:
                print(f"[pagamento] erro ao marcar como pago: {e}")
        elif method == "paypal":
            code = f"PAYPAL{uuid.uuid4().hex[:20]}"
            status = "redirect"
        elif method == "boleto":
            code = f"BOLETO{uuid.uuid4().hex[:20]}"
            status = "waiting"
        else:
            conn.close()
            self.set_status(400)
            return self.write_json({"error": "Método inválido"})

        # Salvar payment
        cursor.execute(
            """INSERT INTO payments 
               (order_id, payment_code, status, created_at) 
               VALUES (?, ?, ?, ?)""",
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
    """
    Handler para listar todos os pedidos (apenas para admin/testes).
    Endpoint: GET /orders
    """
    
    def write_json(self, data):
        """Helper para escrever JSON"""
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data))
    
    def get(self):
        """
        Retorna todas as orders do banco de dados.
        """
        conn = conectar_checkout()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
        orders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        self.write_json({"orders": orders, "total": len(orders)})

