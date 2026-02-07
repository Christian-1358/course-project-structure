import tornado.web
from database import usuario_pagou

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user = self.get_secure_cookie("user_id")
        return int(user.decode()) if user else None

    def prepare(self):
        if not self.current_user:
            return

        rota_livre = self.request.path in ["/pagamento", "/pagamento.html", "/confirmar_pagamento"]

        if rota_livre:
            return

        if not usuario_pagou(self.current_user):
            self.redirect("/pagamento.html")
