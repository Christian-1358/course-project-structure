import tornado.web

class Sobre(tornado.web.RequestHandler):
    def get(self):
        self.render(
            "sobre.html",
            erro=None,
            mensagem=None,
            usuario_prefill=""
        )
