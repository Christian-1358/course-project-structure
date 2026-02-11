import os
import sqlite3
import tornado.web
import tornado.ioloop
from datetime import datetime   

# ===============================
# HANDLERS DO USUÁRIO
# ===============================
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

from app.handlers.pagamento import BaseHandler, OrdersHandler, CheckoutHandler, PagamentoPageHandler, MercadoPagoCreateHandler, MercadoPagoWebhookHandler
from app.handlers.certificado import CertificadoViewHandler, CertificadoPDFHandler

# ===============================
# ADMIN
# ===============================
from app.utils.admin_tools import (
    LoginDevHandler, AlterarStatusHandler, 
    BuscarUsuarioHandler,
    ForcarNotasHandler, ComprasHandler, GerarCertificadoHandler, 
    criar_tabela, criar_usuario_admin_se_nao_existe,
    MarcarPagoHandler, RemoverPagamentoHandler, BloquearUsuarioHandler, DesbloquearUsuarioHandler,
    AlterarSenhaHandler, ResetarSenhaHandler
)

# ===============================
# CONFIG
# ===============================
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

        # ===============================
        # ARQUIVOS ESTÁTICOS
        # ===============================
        (r"/static/(.*)", tornado.web.StaticFileHandler, {
            "path": settings["static_path"]
        }),

        # ===============================
        # LOGIN / AUTENTICAÇÃO
        # ===============================
        (r"/?", LoginHandler),
        (r"/login/?", LoginHandler),
        (r"/logout/?", LogoutHandler),
        (r"/auth/google/?", GoogleLoginHandler),
        (r"/criar_conta/?", CriarContaHandler),
        (r"/recuperar_senha/?", RecuperarSenhaHandler),


        # ===============================
        # CONTEÚDO (BLOQUEADO SE NÃO PAGOU)
        # ===============================
        (r"/curso/?", CursoHandler),
        (r"/sobre/?", Sobre),
        (r"/submit/?", SubmitCodeHandler),

        # ===============================
        # PROVAS
        # ===============================
        (r"/prova/([0-9]+)/?", ProvaHandler),
        (r"/recuperacao/([0-9]+)/?", RecuperacaoHandler),
        (r"/prova/final/?", ProvaFinalHandler),

        # ===============================
        # CERTIFICADOS
        # ===============================
        (r"/certificado/([0-9]+)/?", GerarCertificadoHandler),
        (r"/certificado/view/([0-9]+)/?", CertificadoViewHandler),
        (r"/certificado/pdf/([0-9]+)/?", CertificadoPDFHandler),
        (r"/gerar_certificado_final/?", GerarCertificadoHandler, dict(modulo_id="final")),

        # ===============================
        # ADMIN
        # ===============================
        (r"/login_dev/?", LoginDevHandler),
        (r"/admin/buscar_usuario/?", BuscarUsuarioHandler),
        (r"/admin/forcar_notas/?", ForcarNotasHandler),
        (r"/admin/alterar_status/?", AlterarStatusHandler),
        (r"/admin/marcar_pago/?", MarcarPagoHandler),
        (r"/admin/remover_pago/?", RemoverPagamentoHandler),
        (r"/admin/bloquear_usuario/?", BloquearUsuarioHandler),
        (r"/admin/desbloquear_usuario/?", DesbloquearUsuarioHandler),
        (r"/admin/alterar_senha/?", AlterarSenhaHandler),
        (r"/admin/resetar_senha/?", ResetarSenhaHandler),
        (r"/admin/compras/?", ComprasHandler),



        (r"/pagamentotrue/?", PagamentoPageHandler),
        (r"/pagamento/criar/?", MercadoPagoCreateHandler),
        (r"/pagamento/webhook/?", MercadoPagoWebhookHandler),
        (r"/checkout/([a-zA-Z]+)", CheckoutHandler),
        (r"/orders", OrdersHandler),
        (r"/pagamento/?", BaseHandler)
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
    print(f"🔑 Google Login Ativo: {GOOGLE_CLIENT_ID[:15]}...")
    print(f"🔒 Admin: http://localhost:{port}/login_dev\n")

    tornado.ioloop.IOLoop.current().start()
