import tornado.web
from app.handlers.base import require_owner

class RecuperacaoHandler(tornado.web.RequestHandler):
    @require_owner
    def get(self, modulo, nota=None):
        if nota is None:
            nota = "0.0"

        self.render(
            "recuperacao.html",
            modulo=int(modulo),
            nota=nota
        )
