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

        # 1. BUSCA DADOS DO ALUNO NO BANCO 🗄️
        nome = "Usuário"
        inicio = datetime.now().strftime("%d/%m/%Y")
        fim = datetime.now().strftime("%d/%m/%Y")
        concluiu_tudo = False

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            # Buscamos o nome e a data específica do módulo solicitado
            query = f"SELECT COALESCE(nome, username) as nome_exibicao, inicio_curso, fim_modulo{modulo}, fim_modulo5 FROM users WHERE id = ?"
            c.execute(query, (user_id,))
            row = c.fetchone()
            if row:
                nome = row['nome_exibicao']
                inicio = row['inicio_curso'] if row['inicio_curso'] else inicio
                fim = row[f'fim_modulo{modulo}'] if row[f'fim_modulo{modulo}'] else fim
                concluiu_tudo = True if row['fim_modulo5'] else False

        # 2. LÓGICA DE SEPARAÇÃO (MÓDULOS 1-5 vs FINAL) 🧠
        
        # --- CASO A: CERTIFICADOS DE MÓDULO (1 ao 5) ---
        if modulo <= 5:
            conteudos = {
                1: "Visão Geral 2026, Dicionário do Milheiro, Cálculo de CPM, Livelo e Esfera, Cias Aéreas.",
                2: "Ranking de Cartões, Zerar Anuidade, Salas VIP, Seguros Gratuitos, Upgrade de Limite.",
                3: "Compras 10x1, Compra de Pontos, Bônus de 100%, Clubes de Milhas, Gestão de CPFs.",
                4: "Tabela Fixa, Classe Executiva, Stopover, Iberia Plus, Regras de CPF, ALL Accor.",
                5: "Venda em Balcão, Venda Particular, Gestão de Lucro, Imposto de Renda, Mentoria Final."
            }
            ementa = conteudos.get(modulo, "Especialista em Estratégias MilhasPRO")

            # Se o usuário clicar em download, gera o PDF do módulo
            if download:
                return self.gerar_pdf_modulo(nome, modulo, ementa, inicio, fim)
            
            # Caso contrário, apenas mostra o HTML na tela
            return self.render("certificado.html", nome=nome, modulo=modulo, ementa=ementa, inicio=inicio, fim=fim, is_pdf=False)

        # --- CASO B: CERTIFICADO FINAL (Módulo 6) ---
        elif modulo == 6:
            if not concluiu_tudo:
                self.write("<script>alert('Você precisa concluir o curso para acessar o certificado final!'); window.location='/curso';</script>")
                return
            
            # Aqui você pode chamar o template 'certificado_final.html' ou gerar o PDF de luxo
            return self.render("certificado_final.html", nome=nome, data=fim)

    def gerar_pdf_modulo(self, nome, modulo, ementa, inicio, fim):
        # Renderiza o HTML para o PDF
        html_content = self.render_string(
            "certificado.html", nome=nome, modulo=modulo, ementa=ementa,
            inicio=inicio, fim=fim, is_pdf=True
        ).decode('utf-8')

        # Seu CSS de alta precisão
        pdf_css = CSS(string="""
            @page { size: A4 landscape; margin: 0; }
            html, body { margin: 0; padding: 0; width: 100%; height: 100%; background: #000; }
            .cert-canvas { width: 297mm; height: 210mm; display: table; background: #000; border: 12mm solid #d4af37; }
            .inner-wrapper { display: table-cell; vertical-align: middle; text-align: center; }
            .student-name { font-size: 40pt; font-weight: bold; color: #fff; border-bottom: 2.5pt solid #d4af37; margin: 12pt auto; width: 75%; }
            h1 { font-size: 50pt; color: #d4af37; text-transform: uppercase; }
        """)

        pdf_file = BytesIO()
        HTML(string=html_content, base_url=BASE_DIR).write_pdf(pdf_file, stylesheets=[pdf_css])
        pdf_file.seek(0)
        self.set_header("Content-Type", "application/pdf")
        self.set_header("Content-Disposition", f'attachment; filename="Certificado_M{modulo}_{nome}.pdf"')
        self.write(pdf_file.read())