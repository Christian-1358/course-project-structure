"""
EXEMPLO DE INTEGRAÇÃO - Como adicionar as rotas de segurança no server.py

Este arquivo mostra exatamente como integrar os novos handlers de segurança
de certificados na sua aplicação.
"""

# ============================================================
# 1. IMPORTAR OS NOVOS HANDLERS
# ============================================================

from app.handlers.verificar_certificado import (
    VerificarCertificadoHandler,
    VerificarCertificadoAdminHandler
)

# ============================================================
# 2. ADICIONAR AS ROTAS (no seu server.py existente)
# ============================================================

"""
Encontre o lugar onde você define as rotas (geralmente no main ou create_app):

handlers = [
    # ... suas rotas existentes ...
    (r"/", MainPageHandler),
    (r"/login", LoginHandler),
    (r"/certificado/([0-9]+)", CertificadoViewHandler),
    (r"/certificado/pdf/([0-9]+)", CertificadoPDFHandler),
    
    # ADICIONE ESTAS DUAS LINHAS:
    (r"/verificar-certificado", VerificarCertificadoHandler),
    (r"/admin/certificado/historico", VerificarCertificadoAdminHandler),
    
    # ... resto das rotas ...
]
"""

# ============================================================
# 3. INICIALIZAR AS TABELAS (execute uma única vez)
# ============================================================

"""
No seu arquivo de inicialização (db_init.py, init_db.py ou similar),
adicione isto:

from app.utils.certificado_security import criar_tabelas_seguranca

def inicializar_banco():
    # ... sua inicialização existente ...
    
    # Criar tabelas de segurança de certificados
    criar_tabelas_seguranca()
    print("✅ Banco de dados inicializado com segurança de certificados")

# E chame a função:
if __name__ == "__main__":
    inicializar_banco()
"""

# ============================================================
# 4. EXEMPLOS DE USO
# ============================================================

"""
VISUALIZAR CERTIFICADO (tela do usuário):
URL: GET /certificado/2
Resultado: 
  - Token único é gerado
  - Hash é calculado
  - Acesso é registrado em auditoria
  - Certificado exibido com ID único

BAIXAR EM PDF (tela do usuário):
URL: GET /certificado/pdf/2
Resultado:
  - Mesmo processo acima
  - PDF é gerado
  - Download é registrado como "download_pdf" na auditoria

VERIFICAR AUTENTICIDADE (terceiros/público):
URL: GET /verificar-certificado?token=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
Resultado:
  {
    "valido": true,
    "certificado": {
      "id": 42,
      "modulo": 3,
      "nota": "45",
      "data_conclusao": "15/02/2026",
      "token": "a1b2c3d4...e5f6",
      "ativo": true
    }
  }

VER HISTÓRICO (admin):
URL: GET /admin/certificado/historico?token=a1b2c3d4...
Resultado: Lista de todos os acessos com IP, tipo, timestamp
"""

# ============================================================
# 5. CÓDIGO COMPLETO DO SERVER.PY (exemplo)
# ============================================================

"""
import tornado.ioloop
import tornado.web
import os

# IMPORTAR HANDLERS DE SEGURANÇA
from app.handlers.verificar_certificado import (
    VerificarCertificadoHandler,
    VerificarCertificadoAdminHandler
)

# ... outras importações ...

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            # Rotas existentes
            (r"/", MainPageHandler),
            (r"/login", LoginHandler),
            (r"/certificado/([0-9]+)", CertificadoViewHandler),
            (r"/certificado/pdf/([0-9]+)", CertificadoPDFHandler),
            
            # NOVAS ROTAS DE SEGURANÇA
            (r"/verificar-certificado", VerificarCertificadoHandler),
            (r"/admin/certificado/historico", VerificarCertificadoAdminHandler),
            
            # ... outras rotas ...
        ]
        
        settings = {
            "template_path": os.path.join(os.path.dirname(__file__), "templates"),
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
            "cookie_secret": "sua-chave-secreta-aqui",
            "login_url": "/login",
            "debug": True,
        }
        
        super().__init__(handlers, **settings)

def make_app():
    return Application()

if __name__ == "__main__":
    # Inicializar banco com tabelas de segurança
    from app.utils.certificado_security import criar_tabelas_seguranca
    criar_tabelas_seguranca()
    
    app = make_app()
    app.listen(8888)
    print("🚀 Servidor rodando em http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()
"""

# ============================================================
# 6. TESTANDO (exemplos com curl)
# ============================================================

"""
# Teste 1: Visualizar certificado (requer autenticação)
curl -b cookies.txt http://localhost:8888/certificado/2

# Teste 2: Baixar PDF (requer autenticação)
curl -b cookies.txt -O http://localhost:8888/certificado/pdf/2

# Teste 3: Verificar certificado (público - não requer autenticação)
curl "http://localhost:8888/verificar-certificado?token=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

# Teste 4: Ver histórico de certificado (admin)
curl -b cookies.txt "http://localhost:8888/admin/certificado/historico?token=a1b2c3d4..."
"""

# ============================================================
# 7. VARIÁVEIS DE AMBIENTE (OPCIONAL)
# ============================================================

"""
Se quiser configurar coisas dinamicamente, adicione ao seu .env:

# Segurança de Certificados
CERT_TOKEN_LENGTH=32          # Comprimento do token (padrão: 32)
CERT_HASH_ALGORITHM=sha256    # Algoritmo de hash (padrão: sha256)
CERT_BLOCK_ATTEMPTS=5         # Tentativas antes de bloquear IP (padrão: 5)
CERT_BLOCK_TIMEOUT=300        # Timeout em segundos (padrão: 300 = 5 min)
CERT_MAX_AGE=2592000          # Dias que certificado é válido (padrão: 30 dias)
"""

# ============================================================
# 8. MONITORAMENTO (OPCIONAL)
# ============================================================

"""
Para monitorar ataques, você pode consultar a tabela:

import sqlite3

conn = sqlite3.connect("usuarios.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Ver todos os acessos negados
cursor.execute('''
    SELECT ip_address, COUNT(*) as tentativas, MAX(timestamp) as ultimo_acesso
    FROM auditoria_certificados
    WHERE tipo_acesso LIKE 'denied%'
    GROUP BY ip_address
    ORDER BY tentativas DESC
''')

print("Tentativas de acesso negado:")
for row in cursor.fetchall():
    print(f"IP {row['ip_address']}: {row['tentativas']} tentativas (último: {row['ultimo_acesso']})")

conn.close()
"""

# ============================================================
# 9. ALERTAS (OPCIONAL)
# ============================================================

"""
Para criar alertas automáticos quando fraude é detectada:

from app.utils.certificado_security import detectar_acesso_suspeito, bloquear_ip

def verificar_suspeitas(ip_address):
    if detectar_acesso_suspeito(ip_address, limite_tentativas=5):
        bloquear_ip(ip_address, "Múltiplas tentativas de acesso não autorizado")
        print(f"⚠️ ALERTA: IP {ip_address} foi bloqueado!")
        
        # TODO: Enviar email para admin
        # enviar_email_admin(f"IP {ip_address} bloqueado por atividade suspeita")
"""

# ============================================================
# 10. INTEGRAÇÃO COM FRONTEND (JavaScript)
# ============================================================

"""
<!-- Botão para compartilhar certificado seguramente -->
<button onclick="compartilharCertificado()">
  Compartilhar Certificado Seguro
</button>

<script>
async function compartilharCertificado() {
    const token = document.getElementById('cert-token').value;
    const url = `${window.location.origin}/verificar-certificado?token=${token}`;
    
    // Copiar link para clipboard
    navigator.clipboard.writeText(url).then(() => {
        alert('Link copiado! Compartilhe com segurança.');
    });
}

// Ou validar certificado em tempo real
async function validarCertificado(token) {
    const response = await fetch(`/verificar-certificado?token=${token}`);
    const data = await response.json();
    
    if (data.valido) {
        console.log('✅ Certificado válido:', data.certificado);
    } else {
        console.log('❌ Certificado inválido:', data.erro);
    }
}
</script>
"""
