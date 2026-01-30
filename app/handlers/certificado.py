import tornado.web
import sqlite3
import os
import io
from xhtml2pdf import pisa # Biblioteca para converter HTML em PDF profissional

class CertificadoHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user_id")

    @tornado.web.authenticated
    def get(self, modulo):
        user_id = self.current_user.decode()
        
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        DB_PATH = os.path.join(BASE_DIR, "usuarios.db")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        try:
            c.execute(f"SELECT nome, username, inicio_curso, fim_modulo{modulo} FROM users WHERE id = ?", (user_id,))
            user = c.fetchone()
        except Exception:
            conn.close()
            return self.write("Erro no banco de dados.")
        conn.close()

        if not user or not user[3]:
            return self.redirect("/curso")

        nome_aluno = user['nome'] if user['nome'] else user['username'].upper()
        data_inicio = user['inicio_curso'] if user['inicio_curso'] else "---"
        data_fim = user[3]

        ementas = {
            "1": "Fundamentos de Milhagem, Programas de Fidelidade e Acúmulo Orgânico.",
            "2": "Cartões High-End, Salas VIP e Estratégias de Proteção de Preço.",
            "3": "Multiplicação de Pontos, Clubes de Milhas e Estratégias de Giro.",
            "4": "Emissões Internacionais, Tabelas Fixas e Stopover de Luxo.",
            "5": "Gestão de Lucro, Balcão de Milhas e Comercialização Elite."
        }
        aprendizado = ementas.get(str(modulo), "Estratégias Avançadas em Milhas Aéreas.")

        # Se for download, geramos o PDF usando o HTML
        if self.get_argument("download", "false") == "true":
            return self.gerar_pdf_via_html(nome_aluno, modulo, data_inicio, data_fim, aprendizado)
        
        self.render("certificado.html", nome=nome_aluno, modulo=modulo, inicio=data_inicio, fim=data_fim, ementa=aprendizado)

    def gerar_pdf_via_html(self, nome, modulo, inicio, fim, ementa):
        # Renderiza o HTML para uma string
        html_content = self.render_string("certificado.html", 
                                          nome=nome, modulo=modulo, 
                                          inicio=inicio, fim=fim, 
                                          ementa=ementa, is_pdf=True).decode('utf-8')
        
        result = io.BytesIO()
        # Converte o HTML em PDF preservando o CSS
        pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=result)
        
        if pisa_status.err:
            return self.write("Erro ao gerar PDF profissional.")

        result.seek(0)
        self.set_header("Content-Type", "application/pdf")
        self.set_header("Content-Disposition", f"attachment; filename=Certificado_M{modulo}.pdf")
        self.write(result.read())
        self.finish()
class CertificadoPDFHandler(CertificadoHandler):
    """Atalho para links antigos [cite: 2026-01-20]"""
    def get(self):
        super().get(modulo="1")