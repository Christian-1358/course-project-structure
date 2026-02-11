import tornado.web

class RecuperacaoHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    @tornado.web.authenticated
    def get(self, modulo, nota=None):
        if nota is None:
            nota = "0.0"

        self.render(
            "recuperacao.html",
            modulo=int(modulo),
            nota=nota
        )
