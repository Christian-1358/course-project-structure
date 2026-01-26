import tornado.web

class Prova1(tornado.web.RequestHandler):
    def get(self):
        self.redirect("Prova_modulo1.html")