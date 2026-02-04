import os
import tornado.web
import tornado.ioloop

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GOOGLE_CLIENT_ID = "899997122020-0v0hokvnet5l9nnt1cufg071tbq60rdc.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"

TORNADO_COOKIE_SECRET = "a9f3d2c1e8f74b6b9c2e0f1a7b8c6d5e123456789"
from app.handlers.sobre import Sobre
from app.handlers.login import LoginHandler, LogoutHandler, GoogleLoginHandler
from app.handlers.curso import CursoHandler
from app.handlers.recuperar_senha import RecuperarSenhaHandler
from app.handlers.emails_logados import EmailsLogadosHandler
from app.handlers.avaliacao import SubmitCodeHandler
from app.handlers.criar_conta import CriarContaHandler
from app.handlers.prova import ProvaHandler
from app.utils.admin_tools import (
    LoginDevHandler,
    AlterarStatusHandler,
    AlterarSenhaHandler,
    ResetarSenhaHandler,
    DeletarUsuarioHandler,
    BuscarUsuarioHandler,
    ComprasHandler,
    criar_tabela,
 
    criar_usuario_admin_se_nao_existe
)



#from app.handlers.certificado import CertificadoPDFHandler

from app.handlers.certificado import (
    CertificadoHandler,
    
)

from app.handlers.prova import ProvaHandler
from app.handlers.recuperacao import RecuperacaoHandler
from app.handlers.pagamento_mensal import PagamentoMensalPage, CriarPagamentoHandler, WebhookHandler
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
            "secret": GOOGLE_CLIENT_SECRET,
        },
    )
    return tornado.web.Application([
        (r"/pagamento", PagamentoMensalPage),                
        (r"/pagamento_mensal", PagamentoMensalPage),
        (r"/pagamento/criar", CriarPagamentoHandler),
        (r"/pagamento/webhook", WebhookHandler),
        (r"/criar-pagamento", CriarPagamentoHandler),       
        (r"/sobre", Sobre),
        (r"/login_dev", LoginDevHandler),
        (r"/admin/alterar_status", AlterarStatusHandler),
        (r"/admin/alterar_senha", AlterarSenhaHandler),
        (r"/admin/resetar_senha", ResetarSenhaHandler),
        (r"/admin/deletar_usuario", DeletarUsuarioHandler),
        (r"/admin/buscar_usuario", BuscarUsuarioHandler),
        (r"/criar_conta", CriarContaHandler),
        (r"/logout", LogoutHandler),
        (r"/", LoginHandler),
        (r"/login", LoginHandler),
        (r"/recuperar_senha", RecuperarSenhaHandler),
        (r"/auth/google", GoogleLoginHandler),
        (r"/curso", CursoHandler),
        (r"/submit", SubmitCodeHandler),
        (r"/admin/emails_logados", EmailsLogadosHandler),
        (r"/admin/compras", ComprasHandler),

        # Rotas de provas antigas
        (r"/prova/([0-9]+)", ProvaHandler),
        (r"/certificado\.html", CertificadoHandler, dict(modulo_padrao="1")),
        (r"/certificado2\.html", CertificadoHandler, dict(modulo_padrao="2")),
        (r"/certificado3\.html", CertificadoHandler, dict(modulo_padrao="3")),
        (r"/certificado4\.html", CertificadoHandler, dict(modulo_padrao="4")),
        (r"/certificado5\.html", CertificadoHandler, dict(modulo_padrao="5")),
        (r"/certificado/([0-9]+)", CertificadoHandler),
        (r"/recuperacao/([0-9]+)", RecuperacaoHandler),


    ], **settings)



if __name__ == "__main__":
    try:
        criar_tabela()
        criar_usuario_admin_se_nao_existe()
        print(" Configuração inicial do DB verificada e usuário 'admin' criado (se necessário).")
    except Exception as e:
        print(f" Erro crítico na inicialização do DB: {e}")

    app = make_app()
    app.listen(8080)
    print(" Servidor rodando em: http://localhost:8080")
    print("Acesse o Painel Admin em: http://localhost:8080/login_dev")
    tornado.ioloop.IOLoop.current().start()