arrumar isso do mercado pago, e fazer isso dar certo 
. Obter sua Credencial (Onde mora o seu Pix)

    Acesse o painel Mercado Pago Developers [cite: 2026-01-20].

    Vá em Credenciais de Produção [cite: 2026-01-20].

    Copie o campo Access Token (uma chave longa que começa com APP_USR-...) [cite: 2026-01-20].

    Importante: Verifique se sua conta no Mercado Pago tem uma chave Pix cadastrada (CPF, E-mail ou Aleatória) para que o recebimento seja processado [cite: 2026-01-20].


Para gerar o seu Access Token e as demais credenciais necessárias para que o Pix caia na sua conta, você deve acessar o portal oficial de desenvolvedores do Mercado Pago.

Aqui estão os links diretos e as instruções profissionais para você configurar seu checkout agora:
1. Links Oficiais para Credenciais

    Painel de Credenciais: https://www.mercadopago.com.br/developers/panel/credentials [cite: 2026-01-20]

        Neste link, você encontrará o Access Token (usado no seu arquivo .py) e a Public Key (usada no seu .html) [cite: 2026-01-20].

    Documentação do Pix: https://www.mercadopago.com.br/developers/pt/docs/checkout-api/integration-configuration/pix [cite: 2026-01-20]
import tornado.web
import sqlite3
import os
import requests
import json
from datetime import datetime

# Localização do banco de dados
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(BASE_DIR, "usuarios.db")

# DADOS OBRIGATÓRIOS: Cole seu Access Token gerado no link acima
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
        # Renderiza com variáveis nulas para evitar erro de 'not defined' no HTML [cite: 2026-01-20]
        self.render("pagamento.html", pix_code=None, qr_img=None)

class ConfirmarPagamentoHandler(tornado.web.RequestHandler):
    """Gera o pagamento real via API vinculada ao seu CPF/Conta [cite: 2026-01-20]"""
    async def post(self):
        user_id = self.get_secure_cookie("user_id")
        if not user_id: 
            self.set_status(403)
            return
        
        user_id_int = int(user_id.decode())
        
        # Estrutura de dados profissional para o Mercado Pago [cite: 2026-01-20]
        payload = {
            "transaction_amount": 49.90,
            "description": "Matricula MentorMilhas Elite",
            "payment_method_id": "pix",
            "external_reference": str(user_id_int),
            "payer": {
                "email": "aluno@mentormilhas.com", # Email do pagador exigido pela API [cite: 2026-01-20]
                "first_name": "Aluno",
                "last_name": "Premium"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                "https://api.mercadopago.com/v1/payments",
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            data = response.json()
            
            if response.status_code == 201:
                # Extrai o código 'Copia e Cola' e a imagem em Base64 [cite: 2026-01-20]
                pix_code = data['point_of_interaction']['transaction_data']['qr_code']
                qr_img = data['point_of_interaction']['transaction_data']['qr_code_base64']
                self.render("pagamento.html", pix_code=pix_code, qr_img=qr_img)
            else:
                self.write(f"Erro na API: {data.get('message', 'Erro desconhecido')}")
        except Exception:
            self.write("Falha na conexão com o sistema de pagamentos.")

class CheckStatusHandler(tornado.web.RequestHandler):
    """Verifica se o aluno já pagou para redirecionar automaticamente [cite: 2026-01-20]"""
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