import tornado.web
from app.utils.security import set_flow_allowed


class StartProvaHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    @tornado.web.authenticated
    def get(self, modulo):
        user = self.current_user
        # aceita 'final' ou número
        try:
            mod = int(modulo)
            set_flow_allowed(self, 'prova', mod)
            self.redirect(f"/prova/{mod}")
            return
        except Exception:
            if modulo == 'final':
                # seta fluxo para final e redireciona para rota final
                set_flow_allowed(self, 'prova', 'final')
                self.redirect("/prova/final")
                return
            # falha: redireciona ao curso
            self.redirect("/curso")


class StartCertificadoHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    @tornado.web.authenticated
    def get(self, modulo):
        user = self.current_user
        mod = int(modulo)
        set_flow_allowed(self, 'certificado', mod)
        self.redirect(f"/certificado/{mod}")
