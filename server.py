
#ARRUMAR O BUG QUE TEM QUE QUANDO A PESSOA GERA O CERTIFICADO QUE N SEJA O FINAL (DOS MODULOS 1 2 3 ETC, ) A PESSOA GERA O CERTIFIADO_FINAL ARRUMAR ISSO, PARA QUE GERE OS CERTIFICAODS DOS OUTROS MODULOS


import os
import sqlite3
import tornado.web
import tornado.ioloop
from datetime import datetime

# Importações dos seus handlers (Certifique-se que os caminhos estão corretos)
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

# Importação do Gerador Profissional (admin_tools.py)
from app.utils.admin_tools import (
    LoginDevHandler, AlterarStatusHandler, AlterarSenhaHandler,
    ResetarSenhaHandler, DeletarUsuarioHandler, BuscarUsuarioHandler,
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
        # Estrutura corrigida para evitar KeyError: 'google_oauth'
        google_oauth={
            "key": GOOGLE_CLIENT_ID, 
            "secret": GOOGLE_CLIENT_SECRET
        },
    )
    
    return tornado.web.Application([
        # --- NAVEGAÇÃO BÁSICA ---
        (r"/", LoginHandler),
        (r"/login", LoginHandler),
        (r"/logout", LogoutHandler),
        (r"/sobre", Sobre),
        (r"/curso", CursoHandler),
        (r"/criar_conta", CriarContaHandler),
        (r"/recuperar_senha", RecuperarSenhaHandler),
        (r"/auth/google", GoogleLoginHandler),
        (r"/submit", SubmitCodeHandler),
        (r"/pagamento", PagamentoMensalPage),
        
        # --- PROVAS E RECUPERAÇÃO ---
        (r"/prova/([0-9]+)", ProvaHandler),
        (r"/recuperacao/([0-9]+)", RecuperacaoHandler),

        # --- SISTEMA DE CERTIFICADOS UNIFICADO ---
        # Esta rota aceita o ID (1-5 para módulos, 6 para final)
        # O GerarCertificadoHandler decide se renderiza o HTML simples ou o PDF Luxuoso
        (r"/certificado/([0-9]+)", GerarCertificadoHandler),
        (r"/gerar_certificado_final", GerarCertificadoHandler),

        # --- PAINEL ADMINISTRATIVO ---

            (r"/login_dev", LoginDevHandler),
        (r"/admin/buscar_usuario", BuscarUsuarioHandler),
        (r"/admin/forcar_notas", ForcarNotasHandler),
        (r"/admin/alterar_status", AlterarStatusHandler),
        (r"/admin/compras", ComprasHandler),
    ], **settings)

if __name__ == "__main__":
    # Inicialização do Banco de Dados
    try:
        criar_tabela()
        criar_usuario_admin_se_nao_existe()
    except Exception as e:
        print(f"Erro ao iniciar DB: {e}")

    app = make_app()
    port = 8080
    app.listen(port)
    print(f"🚀 Sistema Mestre das Milhas Online: http://localhost:{port}")
    print(f"🛡️ Segurança de URL Ativada: IDs manuais serão validados via Cookie.")
    tornado.ioloop.IOLoop.current().start()


