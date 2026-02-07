import os
import sqlite3
import tornado.ioloop
import tornado.web
from datetime import datetime

try:
    from weasyprint import HTML
except ImportError:
    HTML = None

# ================== CONFIG ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

def render_html_certificado(nome, modulo, ementa, inicio, fim, is_pdf=False):
    # Botão só aparece na visualização do navegador (HTML)
    btn_html = f'''
    <div class="acoes" style="text-align:center; margin-top:20px;">
        <a class="btn" href="/certificado_pdf/{modulo}" 
           style="background:#d4b038; color:#000; padding:15px 25px; text-decoration:none; font-weight:bold; border-radius:5px;">
           ⬇ BAIXAR CERTIFICADO EM PDF
        </a>
    </div>
    ''' if not is_pdf else ''

    # Ajuste de escala para PDF (A4 Landscape)
    zoom_style = "zoom: 0.75;" if is_pdf else ""

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <style>
        @page {{ size: A4 landscape; margin: 0; }}
        body {{ margin: 0; padding: 0; background: {('#fff' if is_pdf else '#000')}; font-family: "DejaVu Serif", serif; }}
        .viewer {{ min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; {zoom_style} }}
        .certificado {{ 
            width: 1123px; height: 794px; background: #000;
            border: 20px solid #d4b038; padding: 14px; position: relative; box-sizing: border-box;
        }}
        .inner {{ 
            width: 100%; height: 100%; border: 2px solid #d4b038; 
            padding: 70px 100px; text-align: center; color: #eaeaea; box-sizing: border-box;
        }}
        .titulo {{ font-size: 52px; color: #d4b038; margin-bottom: 12px; }}
        .nome {{ font-size: 38px; font-weight: bold; color: #fff; margin: 26px 0; }}
        .nome span {{ border-bottom: 2px solid #d4b038; padding: 0 20px 5px; }}
        .rodape {{ margin-top: 45px; font-size: 14px; color: #888; }}
    </style>
</head>
<body>
    <div class="viewer">
        <div class="certificado">
            <div class="inner">
                <div style="letter-spacing: 6px; margin-bottom: 30px; color:#d4b038;">MILHASPRO</div>
                <div class="titulo">CERTIFICADO</div>
                <div class="nome"><span>{nome}</span></div>
                <p style="font-size:20px;">Concluiu com êxito o Módulo {modulo}: {ementa}</p>
                <div class="rodape">PERÍODO: {inicio} ATÉ {fim}</div>
            </div>
        </div>
        {btn_html}
    </div>
</body>
</html>
"""

class CertificadoViewHandler(tornado.web.RequestHandler):
    def get(self, modulo_id):
        # Aqui você buscaria no banco. Exemplo estático:
        html = render_html_certificado("NOME DO ALUNO", modulo_id, "Expert em Milhas", "01/01/2026", "07/02/2026", False)
        self.write(html)

class CertificadoPDFHandler(tornado.web.RequestHandler):
    def get(self, modulo_id):
        if not HTML:
            self.set_status(500)
            self.write("Erro: Biblioteca WeasyPrint não encontrada.")
            return

        try:
            # 1. Gera o HTML focado para PDF
            html_content = render_html_certificado("NOME DO ALUNO", modulo_id, "Expert em Milhas", "01/01/2026", "07/02/2026", True)
            
            # 2. Transforma em PDF (bytes)
            pdf_bytes = HTML(string=html_content).write_pdf()

            # 3. Configura headers de resposta
            self.set_header("Content-Type", "application/pdf")
            self.set_header("Content-Disposition", f"attachment; filename=Certificado_Modulo_{modulo_id}.pdf")
            self.set_header("Content-Length", len(pdf_bytes))
            
            # 4. Envia o binário
            self.write(pdf_bytes)
            
        except Exception as e:
            self.set_status(500)
            self.write(f"Erro ao gerar PDF: {str(e)}")
