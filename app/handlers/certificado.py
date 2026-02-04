from weasyprint import HTML, CSS
from io import BytesIO
from datetime import datetime
import tornado.web
import sqlite3
import os

BASE_DIR = os.path.abspath(os.getcwd())
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

class CertificadoHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id")
        if user_id:
            try: return int(user_id.decode())
            except: return None
        return None

    @tornado.web.authenticated
    def get(self, modulo):
        user_id = self.current_user
        modulo = int(modulo)
        download = self.get_argument("download", None)

        # EMENTAS REAIS EXTRAÍDAS DAS SUAS IMAGENS
        conteudos = {
            1: "Visão Geral 2026, Dicionário do Milheiro, Cálculo de CPM, Livelo e Esfera, Cias Aéreas, Alertas Técnicos e Primeiro Acúmulo.",
            2: "Ranking de Cartões, Zerar Anuidade, Salas VIP, Seguros Gratuitos, Cooperativas, Upgrade de Limite, Spread Zero e Proteção de Preço.",
            3: "Compras 10x1, Compra de Pontos, Bônus de 100%, Clubes de Milhas, Milhas no Tanque, Parceiros Varejo, Gestão de CPFs e Giro de Boletos.",
            4: "Tabela Fixa, Classe Executiva, Stopover, Iberia Plus, Regras de CPF, Destinos EUA, Taxas de Combustível e ALL Accor.",
            5: "Venda em Balcão, Venda Particular, Gestão de Lucro, Imposto de Renda, Agência Digital, Reinvestimento, Tendências 2026 e Mentoria Final."
        }
        
        ementa_detalhada = conteudos.get(modulo, "Especialista em Estratégias MilhasPRO")
        nome = "Usuário"
        inicio = datetime.now().strftime("%d/%m/%Y")
        fim = datetime.now().strftime("%d/%m/%Y")

        if user_id:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                # SQL Robusto: busca Nome ou Username caso nome esteja vazio
                query = f"SELECT COALESCE(nome, username) as nome_exibicao, inicio_curso, fim_modulo{modulo} FROM users WHERE id = ?"
                c.execute(query, (user_id,))
                row = c.fetchone()
                if row:
                    nome = row['nome_exibicao']
                    inicio = row['inicio_curso'] if row['inicio_curso'] else inicio
                    fim = row[f'fim_modulo{modulo}'] if row[f'fim_modulo{modulo}'] else fim

        if download:
            html_content = self.render_string(
                "certificado.html",
                nome=nome, modulo=modulo, ementa=ementa_detalhada,
                inicio=inicio, fim=fim, is_pdf=True
            ).decode('utf-8')

            # CSS DE ALTA PRECISÃO - CENTRALIZAÇÃO VERTICAL E HORIZONTAL TOTAL
            pdf_css = CSS(string="""
                @page { 
                    size: A4 landscape; 
                    margin: 0; 
                }
                html, body { 
                    margin: 0; padding: 0; 
                    width: 100%; height: 100%; 
                    background: #000; 
                }
                
                .cert-canvas {
                    width: 297mm; height: 210mm;
                    display: table; /* Técnica mais estável para WeasyPrint */
                    background: #000;
                    box-sizing: border-box;
                    border: 12mm solid #d4af37;
                }

                .inner-wrapper {
                    display: table-cell;
                    vertical-align: middle;
                    text-align: center;
                    width: 100%; height: 100%;
                }

                .inner-border {
                    display: inline-block;
                    width: 255mm; height: 170mm;
                    border: 1.2pt solid #c9a63a;
                    padding: 30pt;
                    box-sizing: border-box;
                }

                .logo { font-size: 22pt; font-weight: bold; color: #fff; letter-spacing: 5pt; margin-bottom: 5pt; }
                .logo span { color: #d4af37; }
                
                h1 { font-size: 50pt; color: #d4af37; letter-spacing: 8pt; margin: 10pt 0; text-transform: uppercase; }
                .subtitle { font-size: 10pt; color: #999; letter-spacing: 3pt; margin-bottom: 15pt; }
                
                .intro { font-size: 15pt; color: #ccc; }
                
                .student-name { 
                    font-size: 40pt; font-weight: bold; color: #fff; 
                    border-bottom: 2.5pt solid #d4af37; padding-bottom: 8pt;
                    margin: 12pt auto; width: 75%;
                }
                
                .description { font-size: 14pt; color: #aaa; width: 85%; line-height: 1.6; margin: 0 auto; }
                
                .ementa-box {
                    color: #f1d592; 
                    font-size: 11pt; 
                    font-style: italic; 
                    margin-top: 12pt;
                    padding: 0 50pt;
                }
                
                .periodo { font-size: 9.5pt; color: #666; text-transform: uppercase; margin-top: 20pt; }
                
                .footer { 
                    width: 100%; margin-top: 30pt;
                    display: table;
                }
                .assinatura { 
                    display: table-cell; width: 33%;
                    border-top: 1pt solid #444; padding-top: 10pt; 
                    font-size: 8pt; color: #777; font-weight: bold;
                }
                .assinatura.center { color: #d4af37; border-top: 1pt solid transparent; }
            """)

            pdf_file = BytesIO()
            HTML(string=html_content, base_url=BASE_DIR).write_pdf(pdf_file, stylesheets=[pdf_css])
            pdf_file.seek(0)

            self.set_header("Content-Type", "application/pdf")
            self.set_header("Content-Disposition", f'attachment; filename="Certificado_M{modulo}_{nome}.pdf"')
            self.write(pdf_file.read())
        else:
            self.render("certificado.html", nome=nome, modulo=modulo, ementa=ementa_detalhada, inicio=inicio, fim=fim, is_pdf=False)