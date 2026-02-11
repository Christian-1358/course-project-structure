from app.utils.admin_tools import conectar  # ajuste se necessário
import tornado.web


def verificar_acesso(handler):
    user_id = handler.get_secure_cookie("user_id")

    if not user_id:
        handler.redirect("/login")
        return False

    user_id = int(user_id.decode())

    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT pago, ativo, bloqueio_motivo FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()

    if not user:
        handler.redirect("/login")
        return False

    # 🔒 Se usuário está bloqueado
    if user["ativo"] == 0:
        motivo = user["bloqueio_motivo"] or "Conta desativada."
        handler.set_status(403)
        handler.write(f"""
            <h1>Conta Bloqueada</h1>
            <p>{motivo}</p>
        """)
        return False

    # 💳 Se não pagou
    if user["pago"] != 1:
        handler.redirect("/pagamento")
        return False

    return True
