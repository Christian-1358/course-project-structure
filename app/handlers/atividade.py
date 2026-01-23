import tornado.web

class AtividadesHandlers(tornado.web.RequestHandler):
    def get(self):
        self.render(
            "atividade.html",

        )
