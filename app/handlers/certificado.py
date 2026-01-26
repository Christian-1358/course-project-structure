import tornado.web
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

BASE_DIR = os.path.abspath(os.getcwd())
DB = os.path.join(BASE_DIR, "usuarios.db")


def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# ================= CERTIFICADO HTML =================
class CertificadoHandler(tornado.web.RequestHandler):
    def get(self):
        user_id = self.get_secure_cookie("user_id")
        nome = self.get_secure_cookie("user")

        if not user_id or not nome:
            self.redirect("/login")
            return

        conn = conectar()
        c = conn.cursor()

        c.execute("""
            SELECT inicio_curso, fim_modulo1
            FROM users
            WHERE id = ?
        """, (int(user_id),))

        dados = c.fetchone()
        conn.close()

        if not dados or not dados["fim_modulo1"]:
            self.redirect("/curso")
            return

        self.render(
            "certificado.html",
            nome=nome.decode(),
            inicio=dados["inicio_curso"],
            fim=dados["fim_modulo1"]
        )


# ================= CERTIFICADO PDF =================
class CertificadoPDFHandler(tornado.web.RequestHandler):
    def get(self):
        user_id = self.get_secure_cookie("user_id")
        nome = self.get_secure_cookie("user")

        if not user_id or not nome:
            self.redirect("/login")
            return

        conn = conectar()
        c = conn.cursor()

        c.execute("""
            SELECT inicio_curso, fim_modulo1
            FROM users
            WHERE id = ?
        """, (int(user_id),))

        dados = c.fetchone()
        conn.close()

        if not dados or not dados["fim_modulo1"]:
            self.redirect("/curso")
            return

        self.set_header("Content-Type", "application/pdf")
        self.set_header(
            "Content-Disposition",
            "attachment; filename=certificado_modulo1.pdf"
        )

        p = canvas.Canvas(self, pagesize=A4)
        w, h = A4

        p.setFont("Helvetica-Bold", 28)
        p.drawCentredString(w / 2, h - 180, "CERTIFICADO")

        p.setFont("Helvetica", 14)
        p.drawCentredString(
            w / 2,
            h - 250,
            f"Certificamos que {nome.decode()}"
        )

        p.drawCentredString(
            w / 2,
            h - 290,
            "concluiu com êxito o Módulo 1 do curso"
        )

        p.drawCentredString(
            w / 2,
            h - 330,
            "Mestre das Milhas"
        )

        p.drawCentredString(
            w / 2,
            h - 380,
            f"Período: {dados['inicio_curso']} até {dados['fim_modulo1']}"
        )

        p.showPage()
        p.save()
