import tornado.web
from app.utils.pagamento_utils import usuario_pagou
from functools import wraps


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


# ===============================
# DECORATORS DE SEGURANÇA
# ===============================

def require_owner(func):
    """
    Decorator que verifica se o usuário logado é o proprietário do recurso.
    Usa user_id do path argument ou querystring para validar proprietário.
    Exemplo: /certificado/view/123 - valida que user autenticado é 123.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        current_user = self.get_current_user()
        if not current_user:
            self.redirect("/login")
            return

        # Tenta extrair user_id do path (primeiro argumento) ou querystring
        user_id_in_path = None
        if args and isinstance(args[0], (int, str)):
            try:
                # Se o primeiro argumento é numérico, tenta como user_id
                user_id_in_path = int(args[0])
            except (ValueError, TypeError):
                pass

        # Se não encontrou no path, tenta na querystring
        if user_id_in_path is None:
            user_id_param = self.get_argument("user_id", None)
            if user_id_param:
                try:
                    user_id_in_path = int(user_id_param)
                except ValueError:
                    pass

        # Se ainda não tem user_id, tenta do certificado_id ou resource_id
        if user_id_in_path is None and args:
            # Assume que o recurso_id está no path e tenta recuperar o usuário via DB
            resource_id = args[0]
            try:
                # Tenta inferir user_id a partir do resource (certificado, prova, etc)
                import sqlite3
                import os
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                db_path = os.path.join(os.path.dirname(BASE_DIR), "usuarios.db")
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Tenta procurar em certificados
                cursor.execute("SELECT user_id FROM certificados WHERE id=? LIMIT 1", (resource_id,))
                row = cursor.fetchone()
                if row:
                    user_id_in_path = row["user_id"]
                
                conn.close()
            except Exception:
                pass

        # Se conseguiu identificar um user_id e não é o do usuário autenticado, bloqueia
        if user_id_in_path is not None and user_id_in_path != current_user:
            self.set_status(403)
            self.write("<h1>Acesso Negado (403)</h1><p>Você não tem permissão para acessar este recurso.</p>")
            return

        # Se passou na validação, executa a função original
        return func(self, *args, **kwargs)

    return wrapper


def require_auth(func):
    """
    Decorator simples que exige autenticação e pagamento.
    Redireciona para login se não estiver autenticado.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        current_user = self.get_current_user()
        if not current_user:
            self.redirect("/login")
            return
        return func(self, *args, **kwargs)

    return wrapper
