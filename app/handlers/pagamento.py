arrumar isso do mercado pago, e fazer isso dar certo 


import tornado.web
import sqlite3
import os
import requests
import json
from datetime import datetime

# Configurações de Diretório e Banco
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(BASE_DIR, "usuarios.db")

# DADOS DE CONFIGURAÇÃO (Substitua pelo seu token do painel de desenvolvedor)
MP_ACCESS_TOKEN = "APP_USR-COLE-SEU-TOKEN-AQUI"

def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

class PagamentoPageHandler(tornado.web.RequestHandler):
    def get(self):
        user_id = self.get_secure_cookie("user_id")
        if not user_id:
            self.redirect("/login")
            return
        # Renderiza a página limpando estados anteriores para evitar erros [cite: 2026-01-20]
        self.render("pagamento.html", pix_code=None, qr_img=None)

class ConfirmarPagamentoHandler(tornado.web.RequestHandler):
    """Gera o pagamento Pix vinculado à sua conta via API [cite: 2026-01-20]"""
    async def post(self):
        user_id = self.get_secure_cookie("user_id")
        if not user_id:
            self.set_status(403)
            return

        user_id_int = int(user_id.decode())

        # Payload profissional exigido pelo Mercado Pago [cite: 2026-01-20]
        payload = {
            "transaction_amount": 49.90,
            "description": "Matricula MentorMilhas Elite",
            "payment_method_id": "pix",
            "external_reference": str(user_id_int),
            "payer": {
                "email": "aluno@mentormilhas.com", # Email do aluno pagador [cite: 2026-01-20]
                "identification": {
                    "type": "CPF",
                    "number": "00000000000" # Opcional: CPF do aluno que está comprando
                }
            }
        }

        headers = {
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            # Requisição para gerar o Pix Real [cite: 2026-01-20]
            response = requests.post(
                "https://api.mercadopago.com/v1/payments",
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            data = response.json()

            if response.status_code == 201:
                pix_code = data['point_of_interaction']['transaction_data']['qr_code']
                qr_img = data['point_of_interaction']['transaction_data']['qr_code_base64']
                # Envia o QR Code gerado para o HTML [cite: 2026-01-20]
                self.render("pagamento.html", pix_code=pix_code, qr_img=qr_img)
            else:
                self.write(f"Erro ao processar: {data.get('message', 'Tente novamente')}")
        except Exception:
            self.write("Erro de conexão com o gateway de pagamento.")

class CheckStatusHandler(tornado.web.RequestHandler):
    """Verifica se o aluno já foi liberado no banco de dados [cite: 2026-01-20]"""
    def get(self):
        user_id = self.get_secure_cookie("user_id")
        if not user_id: 
            self.write({"status": "error"})
            return
        
        conn = conectar()
        user = conn.execute("SELECT pago FROM users WHERE id = ?", (int(user_id.decode()),)).fetchone()
        conn.close()
        
        status = "pago" if user and user['pago'] == 1 else "pendente"
        self.write({"status": status})