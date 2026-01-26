import tornado.web

class CursoHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")

        if not user:
            self.redirect("/login")
            return

        self.render("curso.html", usuario=user.decode())
