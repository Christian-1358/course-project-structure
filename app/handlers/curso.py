import tornado.web

class CursoHandler(tornado.web.RequestHandler):
    def get(self):
        user_id = self.get_secure_cookie("user_id")
        user = self.get_secure_cookie("user")

        if not user_id:
            self.redirect("/login")
            return

        self.render(
            "curso.html",
            usuario=user.decode()
        )
