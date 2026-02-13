import tornado.web
from app.utils.pagamento_utils import usuario_pagou


class DebugStatusHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    @tornado.web.authenticated
    def get(self):
        user_id = self.current_user

        info = {
            "user_id": user_id,
            "secure_cookies": {
                "user": bool(self.get_secure_cookie("user")),
                "user_id": bool(self.get_secure_cookie("user_id")),
            },
            "pagamento": None,
            "flow_cookies": {}
        }

        if user_id:
            try:
                info["pagamento"] = usuario_pagou(user_id)
            except Exception as e:
                info["pagamento"] = f"erro: {e}"

        # checar presença dos cookies de fluxo (sem consumi-los)
        for area in ("prova", "certificado"):
            info["flow_cookies"][area] = {}
            for mod in (1,2,3,4,5,6,'final'):
                name = f"flow_{area}_{mod}"
                info["flow_cookies"][area][str(mod)] = bool(self.get_secure_cookie(name))

        self.set_header('Content-Type', 'application/json')
        self.write(info)
