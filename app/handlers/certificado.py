import os
import sqlite3
import hashlib
import tornado.web
from datetime import datetime
from weasyprint import HTML

# ================== CONFIG ==================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_senha(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# ================== HTML DO CERTIFICADO ==================
def html_certificado(nome, modulo, ementa, inicio, fim):
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Certificado</title>
<style>
body {{
    background: #111;
    color: #fff;
    font-family: Arial, Helvetica, sans-serif;
    margin: 0;
    padding: 0;
}}
.cert {{
    width: 900px;
    height: 600px;
    margin: 40px auto;
    padding: 40px;
    border: 8px solid #00ff99;
    text-align: center;
}}
h1 {{
    color: #00ff99;
    font-size: 42px;
    margin-bottom: 20px;
}}
.nome {{
    font-size: 36px;
    font-weight: bold;
    margin: 30px 0;
}}
.modulo {{
    font-size: 22px;
    margin-top: 20px;
}}
.datas {{
    margin-top: 40px;
    font-size: 16px;
}}
.footer {{
    margin-top: 60px;
    font-size: 14px;
    opacity: 0.8;
}}
</style>
</head>
<body>
<div class="cert">
    <h1>CERTIFICADO</h1>

    <p>Certificamos que</p>

    <div class="nome">{nome}</div>

    <p>concluiu o módulo</p>

    <div class="modulo">
        <strong>Módulo {modulo}</strong><br>
        {ementa}
    </div>

    <div class="datas">
        Início: {inicio} <br>
        Conclusão: {fim}
    </div>

    <div class="footer">
        Elite Milhas • Documento válido
    </div>
</div>
</body>
</html>
"""

# ================== VIEW HTML ==================
class CertificadoViewHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    @tornado.web.authenticated
    def get(self, modulo_id):

        mid = int(modulo_id)
        uid = self.current_user

        conn = conectar()
        c = conn.cursor()

        c.execute("""
            SELECT COALESCE(nome, username) AS nome, inicio_curso
            FROM users WHERE id = ?
        """, (uid,))
        user = c.fetchone()
        conn.close()

        if not user:
            self.redirect("/login")
            return

        nome = user["nome"].upper()
        inicio = user["inicio_curso"] or "01/01/2026"
        fim = datetime.now().strftime("%d/%m/%Y")

        ementas = {
            1: "Visão Geral 2026, CPM, Dicionário",
            2: "Cartões, Anuidade Zero, Salas VIP",
            3: "Compra de Pontos, Bônus, 10x1",
            4: "Executiva, Stopover, Iberia Plus",
            5: "Venda de Milhas, Gestão de Lucro"
        }

        html = html_certificado(
            nome=nome,
            modulo=mid,
            ementa=ementas.get(mid, ""),
            inicio=inicio,
            fim=fim
        )

        self.write(html)

# ================== PDF HANDLER ==================
class CertificadoPDFHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    @tornado.web.authenticated
    def get(self, modulo_id):

        mid = int(modulo_id)
        uid = self.current_user

        conn = conectar()
        c = conn.cursor()

        c.execute("""
            SELECT COALESCE(nome, username) AS nome, inicio_curso
            FROM users WHERE id = ?
        """, (uid,))
        user = c.fetchone()
        conn.close()

        if not user:
            self.set_status(403)
            self.write("Usuário não autorizado")
            return

        nome = user["nome"].upper()
        inicio = user["inicio_curso"] or "01/01/2026"
        fim = datetime.now().strftime("%d/%m/%Y")

        ementas = {
            1: "Visão Geral 2026, CPM, Dicionário",
            2: "Cartões, Anuidade Zero, Salas VIP",
            3: "Compra de Pontos, Bônus, 10x1",
            4: "Executiva, Stopover, Iberia Plus",
            5: "Venda de Milhas, Gestão de Lucro"
        }

        html = html_certificado(
            nome=nome,
            modulo=mid,
            ementa=ementas.get(mid, ""),
            inicio=inicio,
            fim=fim
        )

        pdf = HTML(string=html).write_pdf()

        self.set_header("Content-Type", "application/pdf")
        self.set_header(
            "Content-Disposition",
            f'attachment; filename="certificado_modulo_{mid}.pdf"'
        )
        self.write(pdf)
