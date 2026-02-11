import tornado.web


class GerarCertificadoHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    @tornado.web.authenticated
    def get(self, modulo_id):
        # Apenas redireciona para o certificado HTML
        return self.redirect(f"/certificado/{modulo_id}")
