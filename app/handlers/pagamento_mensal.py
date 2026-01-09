import json
import logging
import random
import time
import os
import tornado.web
# ...existing code...
from app.utils.admin_tools import registrar_compra 

MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")  # TOKEN REAL
PIX_KEY = os.environ.get("PIX_KEY", "000.000.000-00")  # só para fallback DEV

try:
    import mercadopago
except Exception:
    mercadopago = None

def json_response(handler, obj, status=200):
    handler.set_status(status)
    handler.set_header("Content-Type", "application/json; charset=utf-8")
    handler.write(json.dumps(obj))

def make_id():
    return int(time.time() * 1000) + random.randint(0, 999)

PLACEHOLDER_QR_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAn0B9u0pV0sAAAAASUVORK5CYII="
)


class PagamentoMensalPage(tornado.web.RequestHandler):
    def get(self):
        self.render("pagamento_mensal.html")


def pix_fallback(data):
    pid = make_id()
    return {
        "id": pid,
        "status": "pending",
        "transaction_amount": data.get("transaction_amount", 29.99),
        "description": data.get("description", "Plano Mensal"),
        "payer": {"email": data.get("email")},
        "point_of_interaction": {
            "transaction_data": {
                "qr_code_base64": PLACEHOLDER_QR_B64
            }
        },
        "pix_key": PIX_KEY
    }

def boleto_fallback(data):
    pid = make_id()
    return {
        "id": pid,
        "status": "pending",
        "transaction_amount": data.get("transaction_amount", 29.99),
        "description": data.get("description", "Plano Mensal"),
        "payment_url": f"/static/boleto_{pid}.pdf"
    }

def card_fallback(data):
    pid = make_id()
    return {
        "id": pid,
        "status": "approved",
        "transaction_amount": data.get("transaction_amount", 29.99),
        "description": data.get("description", "Plano Mensal"),
        "message": "Pagamento aprovado (DEV)"
    }


class CriarPagamentoHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            data = json.loads(self.request.body.decode())
        except Exception:
            return json_response(self, {"sucesso": False, "mensagem": "JSON inválido"}, 400)

        metodo = (data.get("metodo") or "").lower()
        email = data.get("email") or "cliente@teste.com"

        if not metodo:
            return json_response(self, {"sucesso": False, "mensagem": "Método obrigatório"}, 400)

        if mercadopago and MP_ACCESS_TOKEN:
            try:
                sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

                pagamento = {
                    "transaction_amount": float(data.get("transaction_amount", 29.99)),
                    "description": data.get("description", "Plano Mensal"),
                    "payer": {"email": email}
                }

                if metodo == "pix":
                    pagamento["payment_method_id"] = "pix"
                    r = sdk.payment().create(pagamento)
                    return json_response(self, {"sucesso": True, "response": r["response"]})

                if metodo == "boleto":
                    pagamento["payment_method_id"] = "bolbradesco"
                    r = sdk.payment().create(pagamento)
                    return json_response(self, {"sucesso": True, "response": r["response"]})

                if metodo == "card":
                    pagamento.update({
                        "token": data.get("token"),
                        "payment_method_id": data.get("payment_method_id"),
                        "issuer_id": data.get("issuer_id"),
                        "installments": int(data.get("installments", 1))
                    })
                    r = sdk.payment().create(pagamento)
                    return json_response(self, {"sucesso": True, "response": r["response"]})

                return json_response(self, {"sucesso": False, "mensagem": "Método inválido"}, 400)

            except Exception as e:
                logging.exception("Erro MP")
                return json_response(self, {"sucesso": False, "erro": str(e)}, 500)

        if metodo == "pix":
            return json_response(self, {"sucesso": True, "response": pix_fallback(data)})

        if metodo == "boleto":
            return json_response(self, {"sucesso": True, "response": boleto_fallback(data)})

        if metodo == "card":
            return json_response(self, {"sucesso": True, "response": card_fallback(data)})

        return json_response(self, {"sucesso": False, "mensagem": "Método desconhecido"}, 400)

class WebhookHandler(tornado.web.RequestHandler):
    def post(self):
        logging.info("Webhook recebido: %s", self.request.body.decode())
        self.set_status(200)
        self.finish()

