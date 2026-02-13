import tornado.web

class RecuperacaoHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    @tornado.web.authenticated
    def get(self, modulo):
        # Captura a nota da URL (ex: /recuperacao/1?nota=6)
        nota_aluno = self.get_argument("nota", "0") 
        from app.utils.recuperacao_utils import get_attempt

        # verifica se existe bloqueio para o usuário neste módulo
        user_id = self.current_user
        bloqueado = False
        lock_until = None
        try:
            info = get_attempt(user_id, int(modulo))
            if info and info.get('lock_until'):
                from datetime import datetime
                try:
                    lock_dt = datetime.fromisoformat(info['lock_until'])
                    if lock_dt > datetime.now():
                        bloqueado = True
                        lock_until = info['lock_until']
                except Exception:
                    pass
        except Exception:
            pass

        self.render(
            "recuperacao.html",
            modulo=int(modulo),
            nota=nota_aluno,
            bloqueado=bloqueado,
            lock_until=lock_until
        )   