"""
Handler para Verificação Pública de Certificados
Permite que terceiros verifiquem a autenticidade de um certificado sem login.
"""

import tornado.web
from app.utils.certificado_security import (
    validar_token_certificado,
    verificar_integridade_certificado,
    registrar_acesso_certificado,
    ip_esta_bloqueado
)


class VerificarCertificadoHandler(tornado.web.RequestHandler):
    """
    Endpoint público para verificar autenticidade de certificado.
    Uso: GET /verificar-certificado?token=xyz123
    """

    def get_ip_address(self):
        """Obtém o IP real do cliente (considerando proxies)"""
        ip = self.request.headers.get("X-Forwarded-For")
        if ip:
            return ip.split(",")[0].strip()
        return self.request.remote_ip

    def get(self):
        """Verifica um certificado pelo token"""
        token = self.get_argument("token", None)

        if not token:
            self.set_status(400)
            self.write({
                "valido": False,
                "erro": "Token não fornecido"
            })
            return

        ip_address = self.get_ip_address()

        # ✅ Verificar se IP está bloqueado
        if ip_esta_bloqueado(ip_address):
            self.set_status(403)
            self.write({
                "valido": False,
                "erro": "Acesso bloqueado por suspeita de ataque"
            })
            registrar_acesso_certificado(None, token, ip_address, "denied_ip_bloqueado")
            return

        # ✅ Validar token e integridade
        if not verificar_integridade_certificado(token):
            self.set_status(404)
            self.write({
                "valido": False,
                "erro": "Certificado não encontrado ou inválido"
            })
            registrar_acesso_certificado(None, token, ip_address, "denied_token_invalido")
            return

        # ✅ Obter dados do certificado
        cert = validar_token_certificado(token)

        if not cert:
            self.set_status(404)
            self.write({
                "valido": False,
                "erro": "Certificado não encontrado"
            })
            return

        # ✅ Registrar acesso bem-sucedido
        registrar_acesso_certificado(cert["user_id"], token, ip_address, "verify_publica")

        # ✅ Retornar informações do certificado
        self.set_header("Content-Type", "application/json")
        self.write({
            "valido": True,
            "certificado": {
                "id": cert["id"],
                "modulo": cert["modulo"],
                "nota": f"{cert['nota']}",
                "data_conclusao": cert["data_conclusao"],
                "token": token[:8] + "..." + token[-4:],  # Mostra apenas parte do token
                "ativo": cert["ativo"] == 1
            }
        })


class VerificarCertificadoAdminHandler(tornado.web.RequestHandler):
    """
    Endpoint para administradores verificarem histórico de um certificado.
    Requer autenticação de admin.
    """

    def get_current_user(self):
        """Verifica se usuário é admin"""
        user_id = self.get_secure_cookie("user_id")
        if not user_id:
            return None

        user_id = int(user_id.decode())

        # TODO: Implementar verificação de admin no banco
        # Por enquanto, apenas um exemplo
        return user_id

    @tornado.web.authenticated
    def get(self):
        """Retorna histórico de acessos a um certificado"""
        token = self.get_argument("token", None)

        if not token:
            self.set_status(400)
            self.write({
                "erro": "Token não fornecido"
            })
            return

        # ✅ Verificar se certificado existe
        cert = validar_token_certificado(token)

        if not cert:
            self.set_status(404)
            self.write({
                "erro": "Certificado não encontrado"
            })
            return

        # Aqui você poderia adicionar lógica de permissão
        # Por exemplo: verificar se é admin ou dono do certificado

        from app.utils.certificado_security import obter_historico_certificado

        historico = obter_historico_certificado(token)

        self.set_header("Content-Type", "application/json")
        self.write({
            "token": token,
            "certificado_id": cert["id"],
            "user_id": cert["user_id"],
            "modulo": cert["modulo"],
            "historico_acessos": historico
        })
