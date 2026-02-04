import tornado.web
import sqlite3
import os
import io
from datetime import datetime
from xhtml2pdf import pisa

# ===============================
# CONFIGURAÇÃO
# ===============================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def formatar_data(data):
    if not data:
        return None
    try:
        return datetime.strptime(data, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
    except ValueError:
        return data

# ===============================
# HANDLER CERTIFICADO POR MÓDULO
# ===============================
class CertificadoHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return uid.decode() if uid else None

    @tornado.web.authenticated
    def get(self, modulo):
        modulo = int(modulo)
        user_id = self.current_user
        gerar_pdf = self.get_argument("pdf", None)

        coluna_fim = f"fim_modulo{modulo}"

        conn = conectar()
        try:
            user = conn.execute(f"""
                SELECT nome, inicio_curso, {coluna_fim}
                FROM users
                WHERE id = ?
            """, (user_id,)).fetchone()

            if not user:
                self.write("Usuário não encontrado")
                return

            if not user[coluna_fim]:
                self.write("Módulo ainda não concluído")
                return

            # ===============================
            # EMENTAS POR MÓDULO
            # ===============================
            ementas = {
                1: "Fundamentos de Milhas Aéreas",
                2: "Cartões de Crédito e Pontuação",
                3: "Clube de Milhas e Promoções",
                4: "Emissão Inteligente de Passagens",
                5: "Escala, Stopover e Hacks Avançados"
            }

            dados = {
                "nome": user["nome"],
                "modulo": modulo,
                "ementa": ementas.get(modulo, "Treinamento em Milhas"),
                "inicio": formatar_data(user["inicio_curso"]),
                "fim": formatar_data(user[coluna_fim]),
            }

            # ===============================
            # GERAR PDF
            # ===============================
            if gerar_pdf:
                html = self.render_string(
                    "certificado.html",
                    **dados,
                    is_pdf=True
                )

                pdf = io.BytesIO()
                pisa.CreatePDF(html, dest=pdf)

                self.set_header("Content-Type", "application/pdf")
                self.set_header(
                    "Content-Disposition",
                    f'attachment; filename="certificado_modulo_{modulo}.pdf"'
                )

                self.write(pdf.getvalue())
                return

            # ===============================
            # MOSTRAR HTML
            # ===============================
            self.render(
                "certificado.html",
                **dados,
                is_pdf=False
            )

        finally:
            conn.close()
