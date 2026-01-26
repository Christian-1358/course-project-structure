import tornado.web
class RecuperacaoHandler(tornado.web.RequestHandler):
    def get(self, modulo, nota=None):
        if nota is None:
            nota = "0.0"

        self.render(
            "recuperacao.html",
            modulo=int(modulo),
            nota=nota
        )
