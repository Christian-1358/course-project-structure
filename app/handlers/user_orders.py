import tornado.web
from app.handlers.base import BaseHandler, require_auth
from app.utils.pagamento_utils import conectar_checkout


class UserOrdersHandler(BaseHandler):
    @require_auth
    def get(self):
        user_id = self.get_current_user()
        conn = conectar_checkout()
        c = conn.cursor()
        c.execute("SELECT id, product_name, amount, status, created_at FROM orders WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        rows = c.fetchall()
        conn.close()
        orders = [dict(r) for r in rows]
        self.render("orders.html", orders=orders)
