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

# Definições dos módulos com ementas
MODULOS_INFO = {
    1: {"titulo": "Módulo 1", "ementa": "Fundamentos de Milhas Aéreas", "questoes": 10},
    2: {"titulo": "Módulo 2", "ementa": "Estratégias de Acúmulo", "questoes": 10},
    3: {"titulo": "Módulo 3", "ementa": "Resgate e Transferências", "questoes": 10},
    4: {"titulo": "Módulo 4", "ementa": "Cartões de Crédito Premium", "questoes": 10},
    5: {"titulo": "Módulo 5", "ementa": "Otimização de Pontos", "questoes": 10},
    6: {"titulo": "Prova Final", "ementa": "Mestre das Milhas - Avaliação Completa", "questoes": 50},
}

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def obter_dados_certificado(user_id, modulo):
    """
    Obtém dados do usuário e da prova para gerar certificado.
    """
    conn = conectar()
    
    # Obter dados do usuário
    user = conn.execute("SELECT username, email FROM users WHERE id = ?", (user_id,)).fetchone()
    
    # Obter resultado da prova
    resultado = conn.execute(
        "SELECT nota, data FROM provas_resultado WHERE user_id = ? AND modulo = ?",
        (user_id, modulo)
    ).fetchone()
    
    conn.close()
    
    if not user or not resultado:
        return None
    
    return {
        "nome": user["username"].upper(),
        "email": user["email"],
        "nota": resultado["nota"],
        "data": resultado["data"],
        "modulo": modulo
    }

def render_html_certificado(nome, email, nota, data_conclusao, modulo, is_pdf=False):
    """
    Renderiza HTML do certificado com dados reais.
    """
    mod_info = MODULOS_INFO.get(int(modulo), {})
    titulo_mod = mod_info.get("titulo", f"Módulo {modulo}")
    ementa = mod_info.get("ementa", "Curso Online")
    questoes = mod_info.get("questoes", 10)
    
    # Formatar data
    try:
        if data_conclusao:
            data_obj = datetime.strptime(data_conclusao, "%d/%m/%Y %H:%M:%S")
            data_formatada = data_obj.strftime("%d de %B de %Y").replace("January", "janeiro").replace("February", "fevereiro").replace("March", "março").replace("April", "abril").replace("May", "maio").replace("June", "junho").replace("July", "julho").replace("August", "agosto").replace("September", "setembro").replace("October", "outubro").replace("November", "novembro").replace("December", "dezembro")
        else:
            data_formatada = datetime.now().strftime("%d de %B de %Y").replace("January", "janeiro").replace("February", "fevereiro").replace("March", "março").replace("April", "abril").replace("May", "maio").replace("June", "junho").replace("July", "julho").replace("August", "agosto").replace("September", "setembro").replace("October", "outubro").replace("November", "novembro").replace("December", "dezembro")
    except:
        data_formatada = datetime.now().strftime("%d/%m/%Y")
    
    # Botão só aparece na visualização do navegador (HTML)
    btn_html = f'''
    <div class="acoes" style="text-align:center; margin-top:20px;">
        <a class="btn" href="/certificado/pdf/{modulo}" 
           style="background:#d4b038; color:#000; padding:15px 25px; text-decoration:none; font-weight:bold; border-radius:5px;">
           ⬇ BAIXAR CERTIFICADO EM PDF
        </a>
    </div>
    ''' if not is_pdf else ''

    zoom_style = "zoom: 0.75;" if is_pdf else ""

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <style>
        @page {{ size: A4 landscape; margin: 0; }}
        body {{ margin: 0; padding: 0; background: {('#fff' if is_pdf else '#000')}; font-family: "DejaVu Serif", Georgia, serif; }}
        .viewer {{ min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; {zoom_style}; padding: 20px; }}
        .certificado {{ 
            width: 1200px; height: 800px; background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
            border: 25px solid #d4b038; padding: 0; position: relative; box-sizing: border-box;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }}
        .inner {{ 
            width: 100%; height: 100%; border: 3px solid #d4b038; 
            padding: 60px 80px; text-align: center; color: #e8e8e8; box-sizing: border-box;
            display: flex; flex-direction: column; justify-content: space-between;
        }}
        .header {{ margin-bottom: 30px; }}
        .logo {{ letter-spacing: 8px; font-size: 24px; color: #d4b038; font-weight: bold; margin-bottom: 20px; }}
        .titulo {{ font-size: 56px; color: #d4b038; margin: 20px 0; font-weight: bold; letter-spacing: 2px; }}
        .subtitulo {{ font-size: 16px; color: #aaa; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 30px; }}
        .content {{ flex-grow: 1; display: flex; flex-direction: column; justify-content: center; }}
        .nome {{ font-size: 42px; font-weight: bold; color: #fff; margin: 30px 0 20px 0; }}
        .nome-underline {{ border-bottom: 3px solid #d4b038; padding-bottom: 10px; display: inline-block; min-width: 400px; }}
        .texto {{ font-size: 18px; color: #ddd; line-height: 1.8; margin: 20px 0; }}
        .modulo-info {{ font-size: 16px; color: #aaa; margin: 15px 0; }}
        .nota-info {{ font-size: 16px; color: #d4b038; font-weight: bold; margin: 15px 0; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #d4b038; }}
        .data {{ font-size: 14px; color: #888; letter-spacing: 1px; }}
        .codigo {{ font-size: 11px; color: #666; margin-top: 10px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="viewer">
        <div class="certificado">
            <div class="inner">
                <div class="header">
                    <div class="logo">🏆 MESTRE DAS MILHAS</div>
                    <div class="titulo">CERTIFICADO</div>
                    <div class="subtitulo">DE CONCLUSÃO</div>
                </div>
                
                <div class="content">
                    <div class="texto">Certificamos que</div>
                    <div class="nome">
                        <div class="nome-underline">{nome}</div>
                    </div>
                    <div class="texto">
                        <strong>completou com êxito</strong> o
                    </div>
                    <div class="modulo-info" style="font-size: 20px; color: #d4b038; font-weight: bold;">
                        {titulo_mod}
                    </div>
                    <div class="texto">
                        {ementa}
                    </div>
                    <div class="nota-info">
                        Nota Final: <strong>{int(nota)}/{questoes} pontos</strong>
                    </div>
                </div>
                
                <div class="footer">
                    <div class="data">Concluído em: {data_formatada}</div>
                    <div class="codigo">ID: {modulo}-{nome[:3].upper()}-{int(nota)}</div>
                </div>
            </div>
        </div>
        {btn_html}
    </div>
</body>
</html>
"""

class CertificadoViewHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    @tornado.web.authenticated
    def get(self, modulo_id):

        user_id = self.current_user

        # 🔒 Validar módulo permitido
        try:
            modulo = int(modulo_id)
        except:
            self.set_status(400)
            self.write("Módulo inválido.")
            return

        if modulo not in MODULOS_INFO:
            self.set_status(404)
            self.write("Certificado inexistente.")
            return

        # 🔒 Verificar se usuário está ativo e pagou
        conn = conectar()
        user = conn.execute(
            "SELECT pago, ativo FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not user or user["pago"] != 1 or user["ativo"] != 1:
            conn.close()
            self.set_status(403)
            self.write("<h1>Acesso Negado (403)</h1><p>Conta inativa ou pagamento pendente.</p>")
            return

        # 🔒 Buscar resultado da prova (somente do próprio usuário)
        resultado = conn.execute(
            """SELECT nota, data, aprovado 
               FROM provas_resultado 
               WHERE user_id = ? AND modulo = ?""",
            (user_id, modulo)
        ).fetchone()

        conn.close()

        if not resultado or resultado["aprovado"] != 1:
            self.set_status(403)
            self.write("<h1>Acesso Negado (403)</h1><p>Você ainda não foi aprovado neste módulo.</p>")
            return

        html = render_html_certificado(
            nome=self.get_user_nome(user_id),
            email="",
            nota=resultado["nota"],
            data_conclusao=resultado["data"],
            modulo=modulo,
            is_pdf=False
        )

        self.write(html)

    def get_user_nome(self, user_id):
        conn = conectar()
        user = conn.execute(
            "SELECT username FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        conn.close()
        return user["username"].upper()

class CertificadoPDFHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    @tornado.web.authenticated
    def get(self, modulo_id):

        user_id = self.current_user

        try:
            modulo = int(modulo_id)
        except:
            self.set_status(400)
            self.write("Módulo inválido.")
            return

        if modulo not in MODULOS_INFO:
            self.set_status(404)
            self.write("Certificado inexistente.")
            return

        if not HTML:
            self.set_status(500)
            self.write("WeasyPrint não instalado.")
            return

        conn = conectar()

        user = conn.execute(
            "SELECT username, pago, ativo FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not user or user["pago"] != 1 or user["ativo"] != 1:
            conn.close()
            self.set_status(403)
            self.write("Acesso negado.")
            return

        resultado = conn.execute(
            """SELECT nota, data, aprovado 
               FROM provas_resultado 
               WHERE user_id = ? AND modulo = ?""",
            (user_id, modulo)
        ).fetchone()

        conn.close()

        if not resultado or resultado["aprovado"] != 1:
            self.set_status(403)
            self.write("Você não foi aprovado neste módulo.")
            return

        html_content = render_html_certificado(
            nome=user["username"].upper(),
            email="",
            nota=resultado["nota"],
            data_conclusao=resultado["data"],
            modulo=modulo,
            is_pdf=True
        )

        pdf_bytes = HTML(string=html_content).write_pdf()

        self.set_header("Content-Type", "application/pdf")
        self.set_header(
            "Content-Disposition",
            f"attachment; filename=Certificado_Modulo_{modulo}.pdf"
        )
        self.write(pdf_bytes)
