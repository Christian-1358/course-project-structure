import os
import sqlite3
import tornado.web
import tornado.ioloop
from datetime import datetime   

# Handlers do Usuário
from app.handlers.prova_final import ProvaFinalHandler
from app.handlers.sobre import Sobre
from app.handlers.login import LoginHandler, LogoutHandler, GoogleLoginHandler
from app.handlers.curso import CursoHandler
from app.handlers.recuperar_senha import RecuperarSenhaHandler
from app.handlers.emails_logados import EmailsLogadosHandler
from app.handlers.avaliacao import SubmitCodeHandler
from app.handlers.criar_conta import CriarContaHandler
from app.handlers.prova import ProvaHandler
from app.handlers.recuperacao import RecuperacaoHandler
from app.handlers.pagamento_mensal import PagamentoMensalPage, CriarPagamentoHandler, WebhookHandler

from app.handlers.certificado import CertificadoViewHandler, CertificadoPDFHandler
from app.utils.admin_tools import (
    LoginDevHandler, AlterarStatusHandler, 
    BuscarUsuarioHandler,
    ForcarNotasHandler, ComprasHandler, GerarCertificadoHandler, 
    criar_tabela, criar_usuario_admin_se_nao_existe
)

# Configurações de Caminho
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

# Configurações de Segurança
TORNADO_COOKIE_SECRET = "a9f3d2c1e8f74b6b9c2e0f1a7b8c6d5e123456789"
GOOGLE_CLIENT_ID = "899997122020-0v0hokvnet5l9nnt1cufg071tbq60rdc.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"

def make_app():
    settings = dict(
        template_path=os.path.join(BASE_DIR, "app", "templates"),
        static_path=os.path.join(BASE_DIR, "app", "static"),
        debug=True,
        cookie_secret=TORNADO_COOKIE_SECRET,
        login_url="/login",
        xsrf_cookies=False,
        google_oauth={
            "key": GOOGLE_CLIENT_ID, 
            "secret": GOOGLE_CLIENT_SECRET
        },
    )
    
    return tornado.web.Application([
        # --- NAVEGAÇÃO E AUTENTICAÇÃO ---
        (r"/", LoginHandler),
        (r"/login", LoginHandler),
        (r"/logout", LogoutHandler),
        (r"/auth/google", GoogleLoginHandler),
        (r"/criar_conta", CriarContaHandler),
        (r"/recuperar_senha", RecuperarSenhaHandler),
        
        # --- CONTEÚDO E CURSO ---
        (r"/sobre", Sobre),
        (r"/curso", CursoHandler),
        (r"/submit", SubmitCodeHandler),
        (r"/pagamento", PagamentoMensalPage),
        
        # --- PROVAS E RECUPERAÇÃO ---
        (r"/prova/([0-9]+)", ProvaHandler),
        (r"/recuperacao/([0-9]+)", RecuperacaoHandler),
        (r"/prova_final", ProvaFinalHandler),

        # --- SISTEMA DE CERTIFICADOS (CORRIGIDO) ---
        # Captura o ID do módulo (1 a 5) ou 6 para o Final
        (r"/certificado/([0-9]+)", GerarCertificadoHandler),
(r"/certificado/([0-9]+)", CertificadoViewHandler),
(r"/certificado/pdf/([0-9]+)", CertificadoPDFHandler),

        (r"/admin/buscar_usuario", BuscarUsuarioHandler),
        (r"/admin/forcar_notas", ForcarNotasHandler),
        (r"/admin/alterar_status", AlterarStatusHandler),
        (r"/admin/compras", ComprasHandler),
    ], **settings)

if __name__ == "__main__":
    try:
        criar_tabela()
        criar_usuario_admin_se_nao_existe()
    except Exception as e:
        print(f"Erro ao iniciar DB: {e}")

    app = make_app()
    port = 8080 
    app.listen(port)
    
    print(f"\n🚀 Servidor Online: http://localhost:{port}")
    print(f"📌 Certificados: Utilize /certificado/ID (Ex: /certificado/1 para Módulo 1)")
    print(f"🔑 Admin: http://localhost:{port}/login_dev\n")

    tornado.ioloop.IOLoop.current().start()