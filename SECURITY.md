# Documentação de Segurança

## 1️⃣ Proteção de URLs - Validação de Acesso

### Problema: URL Traversal / Acesso Não Autorizado
Usuários maliciosos poderiam acessar diretamente URLs de recursos que não pertencem a eles, como:
- `/certificado/view/123` (ver certificado de outro usuário)
- `/prova/456` (acessar prova de outro usuário)
- `/recuperacao/789` (tentar recuperação de outro usuário)

### Solução Implementada

#### 1. **Decorator `@require_owner`** (em `app/handlers/base.py`)
Valida que o usuário logado é o proprietário do recurso antes de permitir acesso.

**Como funciona:**
1. Verifica se usuário está autenticado (`get_current_user()`)
2. Extrai o `user_id` do path argument ou querystring
3. Se não encontrar no path, consulta o banco de dados para inferir proprietário
4. **Bloqueia acesso (403)** se o `user_id` no request ≠ `user_id` do usuário autenticado
5. Redireciona para `/login` se não autenticado

**Exemplo:**
```python
class CertificadoViewHandler(tornado.web.RequestHandler):
    @require_owner
    def get(self, modulo_id):
        # Só executa se usuário logado é o proprietário
        html = render_html_certificado(...)
```

### 2. **Decorator `@require_auth`** (em `app/handlers/base.py`)
Simples verificação de autenticação + pagamento (usa `@authenticated` do Tornado).

**Exemplo:**
```python
@require_auth
def some_protected_method(self):
    # Só executa se usuário está autenticado e pagou
    pass
```

### 3. **Handlers Protegidos**
Os seguintes handlers foram protegidos com `@require_owner`:
- ✅ `CertificadoViewHandler` - visualização de certificado
- ✅ `CertificadoPDFHandler` - download de certificado em PDF
- ✅ `ProvaHandler` - acesso a provas
- ✅ `RecuperacaoHandler` - acesso a recuperação

## Exemplos de Bloqueio

### Cenário 1: Acesso ao certificado de outro usuário
```
Usuario A (id=1) tenta acessar: /certificado/view/50
Proprietário real do certificado 50: Usuario B (id=2)

❌ BLOQUEADO → HTTP 403 "Acesso Negado"
```

### Cenário 2: Tentativa sem autenticação
```
Usuario não autenticado tenta acessar: /certificado/view/50

❌ BLOQUEADO → Redireciona para /login
```

### Cenário 3: Acesso válido
```
Usuario A (id=1) tenta acessar: /certificado/view/50
Proprietário do certificado 50: Usuario A (id=1)

✅ PERMITIDO → Exibe certificado
```

## Configuração de Novos Handlers

Para proteger um novo handler, adicione o decorator:

```python
from app.handlers.base import require_owner

class NovoHandler(tornado.web.RequestHandler):
    @require_owner
    def get(self, resource_id):
        # Código aqui só executa se proprietário válido
        pass
```

## Tecnologia Utilizada
- **Framework:** Tornado Web Framework
- **Mecanismo:** Python decorators + secure cookies
- **Validação:** user_id do cookie vs. user_id do recurso
- **Banco:** SQLite (usuarios.db) para inferir proprietário se necessário

## Segurança Adicional Implementada
- ✅ Autenticação obrigatória (secure cookies)
- ✅ Verificação de pagamento (`usuario_pagou()`)
- ✅ Validação de proprietário de recurso
- ✅ Logging de erros de acesso (403)
- ✅ Redirecionamento para login se não autenticado

## Melhorias Futuras
1. **Rate limiting** - limitar tentativas de acesso não autorizado
2. **Auditoria** - registrar tentativas de acesso não autorizado
3. **2FA (Two-Factor Auth)** - adicionar segunda camada de segurança
4. **Tokens expiráveis** - ao invés de cookies permanentes
5. **CSRF protection** - adicionar tokens CSRF para POST/PUT/DELETE
