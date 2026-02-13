from app.utils.admin_tools import conectar  # ajuste se necessário
import tornado.web
import time
import hashlib
from app.utils.pagamento_utils import usuario_pagou


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


def _flow_cookie_name(area, modulo):
    return f"flow_{area}_{modulo}"


def set_flow_allowed_if_referer(handler, area, modulo):
    """
    Se o Referer da requisição for interno ao site, seta um cookie seguro
    que autoriza o acesso ao recurso (prova/certificado) temporariamente.
    """
    referer = handler.request.headers.get("Referer", "")
    host = handler.request.host

    if referer and host in referer:
        # valor curto assinado: timestamp + hash
        ts = str(int(time.time()))
        raw = f"{handler.get_secure_cookie('user_id')}-{area}-{modulo}-{ts}".encode()
        token = hashlib.sha256(raw).hexdigest()
        name = _flow_cookie_name(area, modulo)
        handler.set_secure_cookie(name, f"{ts}:{token}", path="/", httponly=True)
        return True
    return False


def set_flow_allowed(handler, area, modulo):
    """
    Define explicitmente o cookie de autorização de fluxo (útil para endpoints internos
    que preparam o acesso mesmo quando o Referer é ausente).
    """
    try:
        ts = str(int(time.time()))
        raw = f"{handler.get_secure_cookie('user_id')}-{area}-{modulo}-{ts}".encode()
        token = hashlib.sha256(raw).hexdigest()
        name = _flow_cookie_name(area, modulo)
        handler.set_secure_cookie(name, f"{ts}:{token}", path="/", httponly=True)
        return True
    except Exception:
        return False


def consume_flow_allowed(handler, area, modulo, max_age_seconds=60):
    """
    Verifica e consome (apaga) o cookie de autorização de fluxo.
    Retorna True se presente e ainda válida; caso contrário False.
    """
    name = _flow_cookie_name(area, modulo)
    val = handler.get_secure_cookie(name)
    if not val:
        return False

    try:
        val = val.decode() if isinstance(val, bytes) else val
        ts_str, token = val.split(":", 1)
        ts = int(ts_str)
    except Exception:
        handler.clear_cookie(name)
        return False

    # expiração simples
    if int(time.time()) - ts > max_age_seconds:
        handler.clear_cookie(name)
        return False

    # opcional: recomputar hash para conferir origem
    try:
        raw = f"{handler.get_secure_cookie('user_id')}-{area}-{modulo}-{ts}".encode()
        expected = hashlib.sha256(raw).hexdigest()
    except Exception:
        handler.clear_cookie(name)
        return False

    if expected != token:
        handler.clear_cookie(name)
        return False

    # tudo ok: consumir cookie
    handler.clear_cookie(name)
    return True


def verify_flow_and_payment(handler, area, modulo):
    """
    Verifica: usuário autenticado, pagamento OK e fluxo autorizado (referer interno ou cookie de fluxo).
    Em caso de falha escreve resposta apropriada e retorna False.
    """
    # 1) autenticado
    uid = handler.get_secure_cookie("user_id")
    if not uid:
        handler.redirect(handler.get_login_url())
        return False

    try:
        user_id = int(uid.decode()) if isinstance(uid, bytes) else int(uid)
    except Exception:
        handler.clear_cookie("user_id")
        handler.redirect(handler.get_login_url())
        return False

    # 2) pagamento
    try:
        if not usuario_pagou(user_id):
            handler.set_status(403)
            handler.write("<h1>Acesso Negado (403)</h1><p>Pagamento pendente.</p>")
            return False
    except Exception as e:
        print(f"[verify_flow_and_payment] erro ao checar pagamento: {e}")
        handler.set_status(500)
        handler.write("Erro interno ao checar pagamento.")
        return False

    # 3) fluxo (referer interno OU cookie de fluxo)
    try:
        if set_flow_allowed_if_referer(handler, area, modulo):
            return True
        if consume_flow_allowed(handler, area, modulo):
            return True
    except Exception as e:
        print(f"[verify_flow_and_payment] erro ao checar fluxo: {e}")

    # negar por padrão
    handler.set_status(403)
    handler.write("<h1>Acesso Negado (403)</h1><p>Acesso direto por URL não permitido.</p>")
    return False
