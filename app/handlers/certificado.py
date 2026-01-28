import tornado.web
import sqlite3
import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
terminar o certificado, comadno handlers
class CertificadoHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        """Fundamental para o funcionamento do @authenticated [cite: 2026-01-20]"""
        return self.get_secure_cookie("user_id")

    @tornado.web.authenticated
    def get(self, modulo):
        # 1. Recuperação de Identidade
        user_id_cookie = self.current_user
        nome_cookie = self.get_secure_cookie("user")

        if not user_id_cookie or not nome_cookie:
            return self.redirect("/login")

        user_id = int(user_id_cookie.decode())
        nome_aluno = nome_cookie.decode().upper()

        # 2. Localização Dinâmica do Banco de Dados [cite: 2026-01-20]
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        DB_PATH = os.path.join(BASE_DIR, "usuarios.db")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        try:
            # Busca a data de conclusão do módulo específico
            query = f"SELECT fim_modulo{modulo} FROM users WHERE id = ?"
            c.execute(query, (user_id,))
            dados = c.fetchone()
        except Exception:
            conn.close()
            return self.write("<h3>Erro: Coluna do módulo não encontrada. Verifique o banco.</h3>")
        
        conn.close()

        # Validação: Só gera se tiver data de conclusão
        if not dados or not dados[0]:
            return self.redirect("/curso")

        data_conclusao = dados[0]

        # 3. Geração do PDF com seu Design Premium [cite: 2026-01-20]
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(A4))
        w, h = landscape(A4)

        # --- FUNDO E MOLDURA ---
        p.setFillColor(HexColor("#050505")) # Black Premium
        p.rect(0, 0, w, h, fill=1)

        # Marca d'água central
        p.setFont("Helvetica-Bold", 140)
        p.setFillColor(HexColor("#0A0A0A"))
        p.drawCentredString(w/2, h/2 - 50, "MILHASPRO")

        # Bordas Douradas Duplas
        p.setStrokeColor(HexColor("#d4af37"))
        p.setLineWidth(12)
        p.rect(25, 25, w-50, h-50, stroke=1, fill=0)
        p.setLineWidth(1)
        p.rect(40, 40, w-80, h-80, stroke=1, fill=0)

        # --- CABEÇALHO ---
        p.setFillColor(HexColor("#ffffff"))
        p.setFont("Helvetica-Bold", 22)
        p.drawCentredString(w/2, h - 90, "MILHASPRO")

        # --- TÍTULO ---
        p.setFillColor(HexColor("#f1d592")) # Dourado
        p.setFont("Helvetica-Bold", 55)
        p.drawCentredString(w/2, h - 170, "CERTIFICADO")
        
        p.setFillColor(HexColor("#888888"))
        p.setFont("Helvetica", 12)
        p.drawCentredString(w/2, h - 195, f"CONCLUSÃO E ESPECIALIZAÇÃO: MÓDULO {modulo}")

        # --- TEXTO DE CERTIFICAÇÃO ---
        p.setFillColor(HexColor("#cccccc"))
        p.setFont("Helvetica", 18)
        p.drawCentredString(w/2, h/2 + 35, "Certificamos que para os devidos fins de direito")

        # Nome do Aluno
        p.setFillColor(HexColor("#ffffff"))
        p.setFont("Helvetica-Bold", 38)
        p.drawCentredString(w/2, h/2 - 20, nome_aluno)
        
        p.setStrokeColor(HexColor("#d4af37"))
        p.setLineWidth(2)
        p.line(w/2 - 200, h/2 - 30, w/2 + 200, h/2 - 30)

        # Descrição Dinâmica
        p.setFillColor(HexColor("#aaaaaa"))
        p.setFont("Helvetica", 14)
        p.drawCentredString(w/2, h/2 - 70, f"concluiu com êxito o Módulo {modulo} do treinamento MilhasPro,")
        p.drawCentredString(w/2, h/2 - 90, "dominando as estratégias elite de acúmulo e emissões de luxo.")

        # --- RODAPÉ E ASSINATURAS ---
        p.setStrokeColor(HexColor("#444444"))
        p.setLineWidth(1)

        # Assinatura Direção
        p.line(120, 110, 320, 110)
        p.setFillColor(HexColor("#ffffff"))
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(220, 95, "DIRETOR EXECUTIVO")
        p.setFillColor(HexColor("#666666"))
        p.setFont("Helvetica", 8)
        p.drawCentredString(220, 82, "Gestão Estratégica MilhasPro")

        # Selo de Autenticidade
        p.setFillColor(HexColor("#d4af37"))
        p.setFont("Helvetica-Bold", 11)
        p.drawCentredString(w/2, 60, f"AUTENTICADO EM {data_conclusao}")

        # Assinatura Coordenação
        p.line(w-320, 110, w-120, 110)
        p.setFillColor(HexColor("#ffffff"))
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(w-220, 95, "COORDENAÇÃO TÉCNICA")
        p.setFillColor(HexColor("#666666"))
        p.setFont("Helvetica", 8)
        p.drawCentredString(w-220, 82, "Núcleo de Inteligência e Emissões")

        p.showPage()
        p.save()

        # 4. Envio do PDF
        buffer.seek(0)
        self.set_header("Content-Type", "application/pdf")
        self.set_header("Content-Disposition", f"attachment; filename=Certificado_M{modulo}_Elite.pdf")
        self.write(buffer.read())
        self.finish()

class CertificadoPDFHandler(CertificadoHandler):
    """Classe de compatibilidade para links que não usam ID [cite: 2026-01-20]"""
    def get(self):
        super().get(modulo="1")

        