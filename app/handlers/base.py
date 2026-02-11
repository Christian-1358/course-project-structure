import tornado.web
from app.utils.pagamento_utils import usuario_pagou


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_id = self.get_secure_cookie("user_id")
        if not user_id:
            return None
        try:
            uid = int(user_id.decode())
        except Exception:
            return None

        # Só considera o usuário como autenticado se ele já pagou
        try:
            if not usuario_pagou(uid):
                return None
        except Exception:
            # Em caso de erro ao checar pagamento, não autentica
            return None

        return uid
