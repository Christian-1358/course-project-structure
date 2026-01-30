import tornado.web
import sqlite3
import os
from datetime import datetime

class ProvaModulo3Handler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user_id")

    @tornado.web.authenticated
    def get(self):
        # Questões estratégicas baseadas na ementa da imagem
        questoes = [
            {
                "id": 1,
                "pergunta": "Em uma promoção de Compras 10×1 entre Livelo e uma parceira de varejo, ao gastar R$ 2.000,00, quantos pontos você acumularia?",
                "opcoes": ["2.000 pontos", "10.000 pontos", "20.000 pontos", "1.000 pontos"],
                "correta": "20.000 pontos"
            },
            {
                "id": 2,
                "pergunta": "Qual é a estratégia principal do 'Giro de Boletos' no contexto de acúmulo?",
                "opcoes": [
                    "Pagar contas sem ganhar nada",
                    "Utilizar cartões de crédito via apps de pagamento para gerar milhas no gasto orgânico",
                    "Evitar o uso de cartões",
                    "Pagar apenas boletos de bancos físicos"
                ],
                "correta": "Utilizar cartões de crédito via apps de pagamento para gerar milhas no gasto orgânico"
            },
            {
                "id": 3,
                "pergunta": "Sobre a 'Compra de Pontos', quando ela é considerada estratégica?",
                "opcoes": [
                    "Sempre que houver pontos disponíveis",
                    "Apenas quando o custo do milheiro (CPM) é inferior ao valor de venda ou resgate",
                    "Quando não temos limite no cartão",
                    "Nunca é vantajoso comprar pontos"
                ],
                "correta": "Apenas quando o custo do milheiro (CPM) é inferior ao valor de venda ou resgate"
            },
            {
                "id": 4,
                "pergunta": "O que caracteriza uma promoção de 'Bônus de 100%'?",
                "opcoes": [
                    "O banco retira seus pontos",
                    "A transferência de pontos do banco para a companhia aérea dobra o saldo final",
                    "Você ganha 100 milhas fixas",
                    "O valor da passagem cai pela metade"
                ],
                "correta": "A transferência de pontos do banco para a companhia aérea dobra o saldo final"
            },
            {
                "id": 5,
                "pergunta": "Na 'Gestão de CPFs', qual o principal limite imposto pelas companhias aéreas (como a Azul ou Latam)?",
                "opcoes": ["Limite de saldo", "Limite de 5 beneficiários cadastrados para emissão", "Limite de acesso ao site", "Limite de voos por dia"],
                "correta": "Limite de 5 beneficiários cadastrados para emissão"
            }
        ]
        self.render("prova3.html", questoes=questoes)

    @tornado.web.authenticated
    def post(self):
        respostas_corretas = {
            "1": "20.000 pontos",
            "2": "Utilizar cartões de crédito via apps de pagamento para gerar milhas no gasto orgânico",
            "3": "Apenas quando o custo do milheiro (CPM) é inferior ao valor de venda ou resgate",
            "4": "A transferência de pontos do banco para a companhia aérea dobra o saldo final",
            "5": "Limite de 5 beneficiários cadastrados para emissão"
        }
        
        acertos = 0
        for q_id, r_correta in respostas_corretas.items():
            if self.get_argument(f"q{q_id}", "") == r_correta:
                acertos += 1
        
        # Nota mínima 4 de 5 (80%)
        if acertos >= 4:
            user_id = self.current_user.decode()
            data_hoje = datetime.now().strftime("%d/%m/%Y")
            
            BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            conn = sqlite3.connect(os.path.join(BASE_DIR, "usuarios.db"))
            c = conn.cursor()
            # Atualiza o fim do módulo 3 com a data real
            c.execute("UPDATE users SET fim_modulo3 = ? WHERE id = ?", (data_hoje, user_id))
            conn.commit()
            conn.close()
            
            self.write("<script>alert('Aprovado! Módulo 3 Concluído.'); window.location.href='/curso';</script>")
        else:
            self.write("<script>alert('Você errou mais de uma questão. Estude o conteúdo e tente novamente.'); window.history.back();</script>")