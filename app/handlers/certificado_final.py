

import tornado.web
import sqlite3
import os
import io
from xhtml2pdf import pisa  # Import essencial para gerar o PDF

# Definição de caminhos
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

class CertificadoFinalHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user_id")

    def conectar(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @tornado.web.authenticated
    def get(self):
        user_id = self.current_user.decode()
        conn = self.conectar()
        
        try:
            # Busca os dados do usuário para preencher o certificado
            user = conn.execute(
                "SELECT nome, username, inicio_curso, certificado_mestre FROM users WHERE id = ?", 
                (user_id,)
            ).fetchone()
        finally:
            conn.close()

        # Validação: Se não houver data de conclusão, bloqueia o acesso
        if not user or not user['certificado_mestre']:
            return self.write("<script>alert('Acesso negado: Conclua a prova primeiro!'); window.location.href='/curso';</script>")

        dados = {
            "nome": user['nome'] if user['nome'] else user['username'].upper(),
            "inicio": user['inicio_curso'] if user['inicio_curso'] else "2026",
            "fim": user['certificado_mestre']
        }

        # Verifica se o pedido é para download do PDF
        if self.get_argument("download", "false") == "true":
            return self.gerar_pdf(dados)
        
        # Renderiza o HTML no navegador
        self.render("certificado_final.html", **dados)

    def gerar_pdf(self, dados):
        """Converte o HTML renderizado em um PDF binário"""
        # Renderiza o HTML para string
        html_content = self.render_string("certificado_final.html", **dados).decode('utf-8')
        
        # Limpeza para o PDF: removemos a área do botão de download
        if '<div class="download">' in html_content:
            html_content = html_content.split('<div class="download">')[0] + "</div></body></html>"
        
        result = io.BytesIO()
        # Transforma HTML/CSS em PDF
        pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=result)
        
        if pisa_status.err:
            return self.write("Erro ao processar PDF.")

        self.set_header("Content-Type", "application/pdf")
        self.set_header("Content-Disposition", f"attachment; filename=Certificado_Mestre_{dados['nome']}.pdf")
        self.write(result.getvalue())
        self.finish()