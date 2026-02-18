import os
import sqlite3
import tornado.web
import tornado.ioloop
from datetime import datetime   


from app.handlers.prova_final import ProvaFinalHandler
from app.handlers.sobre import Sobre
from app.handlers.login import LoginHandler, LogoutHandler, GoogleLoginHandler
from app.handlers.perfil import PerfilHandler
from app.handlers.user_orders import UserOrdersHandler
from app.handlers.curso import CursoHandler
from app.handlers.recuperar_senha import RecuperarSenhaHandler
from app.handlers.emails_logados import EmailsLogadosHandler
from app.handlers.avaliacao import SubmitCodeHandler
from app.handlers.criar_conta import CriarContaHandler
from app.handlers.prova import ProvaHandler
from app.handlers.recuperacao import RecuperacaoHandler
from app.handlers.flow import StartProvaHandler, StartCertificadoHandler
from app.handlers.debug import DebugStatusHandler
from app.handlers.flow import StartProvaHandler, StartCertificadoHandler

from app.handlers.pagamento import OrdersHandler, CheckoutHandler, PagamentoPageHandler, MercadoPagoCreateHandler, MercadoPagoWebhookHandler
from app.handlers.certificado import CertificadoViewHandler, CertificadoPDFHandler

from app.utils.admin_tools import (
    LoginDevHandler, AlterarStatusHandler, 
    BuscarUsuarioHandler,
    ForcarNotasHandler, ComprasHandler, GerarCertificadoHandler, 
    CheckFinalStatusHandler,
    criar_tabela, criar_usuario_admin_se_nao_existe,
    MarcarPagoHandler, RemoverPagamentoHandler, BloquearUsuarioHandler, DesbloquearUsuarioHandler,
    AlterarSenhaHandler, ResetarSenhaHandler
)
from app.handlers.certificado import CertificadoPDFChromeHandler
from app.handlers.certificado import CertificadoViewHandler, CertificadoPDFHandler

from app.handlers.comentarios import CommentHandler
from app.handlers.public_profile import PublicProfileHandler
from app.handlers.pagamento import MercadoPagoCreateHandler, PagamentoPageHandler
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

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

        (r"/static/(.*)", tornado.web.StaticFileHandler, {
            "path": settings["static_path"]
        }),

    
        (r"/?", LoginHandler),
        (r"/login/?", LoginHandler),
        (r"/logout/?", LogoutHandler),
        (r"/auth/google/?", GoogleLoginHandler),
        (r"/criar_conta/?", CriarContaHandler),
        (r"/recuperar_senha/?", RecuperarSenhaHandler),
        (r"/perfil/?", PerfilHandler),
        (r"/me/orders/?", UserOrdersHandler),

        (r"/curso/?", CursoHandler),
        (r"/sobre/?", Sobre),
        (r"/submit/?", SubmitCodeHandler),


        (r"/prova/([0-9]+)/?", ProvaHandler),
        (r"/prova/final/?", ProvaFinalHandler),
        (r"/start/prova/([0-9a-zA-Z_-]+)/?", StartProvaHandler),
        (r"/start/certificado/([0-9]+)/?", StartCertificadoHandler),
        (r"/debug/status/?", DebugStatusHandler),
        (r"/recuperacao/([0-9]+)/?", RecuperacaoHandler),
        (r"/prova/final/?", ProvaFinalHandler),

        (r"/start/certificado/([0-9]+)/?", StartCertificadoHandler),

        (r"/certificado/([0-9]+)/?", CertificadoViewHandler),
        (r"/certificado/pdf/([0-9]+)/?", CertificadoPDFHandler),
        (r"/certificado/pdf_chrome/([0-9]+)/?", CertificadoPDFChromeHandler),
        (r"/gerar_certificado_final/?", GerarCertificadoHandler, dict(modulo_id="final")),

        (r"/login_dev/?", LoginDevHandler),
        (r"/admin/buscar_usuario/?", BuscarUsuarioHandler),
        (r"/admin/forcar_notas/?", ForcarNotasHandler),
        (r"/admin/check_final_status/?", CheckFinalStatusHandler),
        (r"/admin/alterar_status/?", AlterarStatusHandler),
        (r"/admin/marcar_pago/?", MarcarPagoHandler),
        (r"/admin/remover_pago/?", RemoverPagamentoHandler),
        (r"/admin/bloquear_usuario/?", BloquearUsuarioHandler),
        (r"/admin/desbloquear_usuario/?", DesbloquearUsuarioHandler),
        (r"/admin/alterar_senha/?", AlterarSenhaHandler),
        (r"/admin/resetar_senha/?", ResetarSenhaHandler),
        (r"/admin/compras/?", ComprasHandler),
        (r"/emails_logados/?", EmailsLogadosHandler),


        (r"/pagamento/?", PagamentoPageHandler),
        (r"/pagamento/criar/?", MercadoPagoCreateHandler),
        (r"/pagamento/webhook/?", MercadoPagoWebhookHandler),
        (r"/checkout/([a-zA-Z]+)/?", CheckoutHandler),
        (r"/orders/?", OrdersHandler),

        (r"/certificado/([0-9]+)/?", CertificadoViewHandler),
        (r"/certificado/pdf/([0-9]+)/?", CertificadoPDFHandler),
        (r"/user/([0-9]+)/?", PublicProfileHandler),
        (r"/api/comment/?", CommentHandler),
    ], **settings)


if __name__ == "__main__":
    port = 8080
    app = make_app()
    app.listen(port)

    print("\n" + "=" * 40)
    print(" SISTEMA MILHAS PRO ONLINE")
    print(" http://milhaspro.home")
    print("=" * 40 + "\n")

    tornado.ioloop.IOLoop.current().start()

#key  mercadopago = 


