# Guia de Implementação - Sistema de Segurança para Certificados

## 📋 Resumo

Um sistema completo de segurança foi implementado para proteger certificados contra fraudes, falsificações e acessos não autorizados. O sistema inclui:

- ✅ **Tokens únicos** - Cada certificado recebe um código verificável
- ✅ **Hash de integridade** - Detecta alterações não autorizadas
- ✅ **Auditoria completa** - Registro de todos os acessos
- ✅ **Bloqueio de IPs** - Previne ataques por força bruta
- ✅ **Verificação pública** - Endpoint para terceiros validarem

---

## 🚀 Passos de Implementação

### 1. **Criar as Tabelas de Banco de Dados**

Execute este código Python uma única vez para criar as tabelas:

```python
from app.utils.certificado_security import criar_tabelas_seguranca

# Execute uma única vez
criar_tabelas_seguranca()
```

Ou no terminal:
```bash
python3 -c "from app.utils.certificado_security import criar_tabelas_seguranca; criar_tabelas_seguranca()"
```

Isso criará 3 tabelas:
- **certificados** - Armazena tokens e hashes
- **auditoria_certificados** - Registra acessos
- **ips_bloqueados** - Rastreia IPs suspeitos

### 2. **Adicionar Handlers à Aplicação**

Registre as rotas no seu arquivo `server.py`:

```python
from app.handlers.verificar_certificado import (
    VerificarCertificadoHandler,
    VerificarCertificadoAdminHandler
)

# Na definição das rotas
handlers = [
    # ... rotas existentes ...
    (r"/verificar-certificado", VerificarCertificadoHandler),
    (r"/admin/certificado/historico", VerificarCertificadoAdminHandler),
]
```

### 3. **Usar os Módulos de Segurança**

Os handlers de certificado foram atualizados automaticamente. Agora quando um usuário:

**Visualiza um certificado:**
- Um token único é gerado e armazenado
- Um hash de integridade é criado
- O acesso é registrado na auditoria
- O certificado inclui o ID único

**Baixa em PDF:**
- Mesma validação e registro
- IP do usuário é capturado

---

## 🔐 Funcionalidades Implementadas

### A. Geração de Token Seguro

```python
from app.utils.certificado_security import gerar_token_certificado

token = gerar_token_certificado()
# Resultado: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
```

**Características:**
- 32 caracteres aleatórios (hexadecimais)
- Praticamente impossível de adivinhar
- Único por certificado

### B. Verificação de Integridade

```python
from app.utils.certificado_security import verificar_integridade_certificado

# Valida se o certificado não foi alterado
valido = verificar_integridade_certificado(token, user_id=123)
```

**Como funciona:**
- Cria um hash SHA-256 com dados do certificado
- Compara com o hash salvo no banco
- Retorna False se houver alterações

### C. Auditoria e Rastreamento

```python
from app.utils.certificado_security import registrar_acesso_certificado

registrar_acesso_certificado(
    user_id=123,
    token="a1b2c3d4...",
    ip_address="192.168.1.1",
    tipo_acesso="download_pdf"
)
```

**Tipos de acesso registrados:**
- `view` - Visualização HTML
- `download_pdf` - Download do PDF
- `verify_publica` - Verificação pública
- `denied_*` - Tentativas bloqueadas

### D. Detecção de Ataques

```python
from app.utils.certificado_security import (
    detectar_acesso_suspeito,
    bloquear_ip
)

# Detecta múltiplas tentativas falhas
if detectar_acesso_suspeito("192.168.1.1", limite_tentativas=10):
    bloquear_ip("192.168.1.1", motivo="Múltiplas tentativas")
```

---

## 🌐 Endpoint Público de Verificação

### Usar a API

```bash
GET /verificar-certificado?token=a1b2c3d4...
```

**Resposta de sucesso:**
```json
{
  "valido": true,
  "certificado": {
    "id": 42,
    "modulo": 3,
    "nota": "45",
    "data_conclusao": "15/02/2026 14:30:00",
    "token": "a1b2c3d4...e5f6",
    "ativo": true
  }
}
```

**Resposta de erro:**
```json
{
  "valido": false,
  "erro": "Certificado não encontrado ou inválido"
}
```

### Casos de Uso

1. **Validar certificados de candidatos**
   - Empresas podem verificar autenticidade

2. **Integração com plataformas de crédito**
   - Plataformas de educação podem validar automaticamente

3. **Compartilhamento seguro**
   - Usuários podem compartilhar tokens ao invés de PDFs

---

## 👨‍💼 Painel de Administração

### Ver Histórico de um Certificado

```bash
GET /admin/certificado/historico?token=a1b2c3d4...
```

Retorna todos os acessos e tentativas com IP, timestamp e tipo.

---

## 🛡️ Medidas de Segurança em Detalhe

### 1. **Token Único (32 caracteres)**
- Gerado com `secrets.token_hex(16)`
- Armazenado no banco de dados
- Impossível de adivinhar por força bruta

### 2. **Hash SHA-256**
- Não é reversível
- Qualquer alteração no certificado invalida
- Protege contra modificação de dados

### 3. **Bloqueio de IP**
- Detecta múltiplas tentativas falhas (5+ em 5 min)
- Bloqueia automaticamente IPs suspeitos
- Pode ser desbloqueado manualmente

### 4. **Auditoria Completa**
- IP de cada acesso
- Timestamp preciso
- Tipo de operação
- Permitindo investigação de incidentes

### 5. **Validação de Propriedade**
- Certificado só é acessível pelo dono
- Hash garante não foi alterado
- IP pode ser rastreado para investigar fraudes

---

## 📊 Estrutura de Dados

### Tabela: `certificados`
```sql
CREATE TABLE certificados (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    modulo INTEGER NOT NULL,
    nota INTEGER NOT NULL,
    data_conclusao TEXT,
    token TEXT UNIQUE NOT NULL,        -- Token de 32 caracteres
    hash TEXT NOT NULL,                -- SHA-256
    data_geracao TEXT NOT NULL,
    ativo INTEGER DEFAULT 1             -- Para revogar certificados
)
```

### Tabela: `auditoria_certificados`
```sql
CREATE TABLE auditoria_certificados (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    token_certificado TEXT,
    ip_address TEXT,
    tipo_acesso TEXT,
    timestamp TEXT NOT NULL
)
```

### Tabela: `ips_bloqueados`
```sql
CREATE TABLE ips_bloqueados (
    id INTEGER PRIMARY KEY,
    ip_address TEXT UNIQUE NOT NULL,
    motivo TEXT,
    data_bloqueio TEXT NOT NULL,
    ativo INTEGER DEFAULT 1
)
```

---

## 🧪 Testando o Sistema

### Teste 1: Criar um Certificado

```python
from app.utils.certificado_security import registrar_certificado

cert = registrar_certificado(
    user_id=1,
    modulo=2,
    nota=45,
    data_conclusao="15/02/2026 14:30:00"
)

print(f"Token: {cert['token']}")
print(f"Hash: {cert['hash']}")
```

### Teste 2: Validar Token

```python
from app.utils.certificado_security import validar_token_certificado

cert = validar_token_certificado("a1b2c3d4...")
if cert:
    print(f"Certificado válido! Módulo: {cert['modulo']}")
else:
    print("Certificado inválido!")
```

### Teste 3: Verificar Integridade

```python
from app.utils.certificado_security import verificar_integridade_certificado

if verificar_integridade_certificado("a1b2c3d4...", user_id=1):
    print("Certificado não foi alterado!")
else:
    print("⚠️ Certificado foi modificado!")
```

---

## 🚨 Tratamento de Emergências

### Se um certificado for comprometido

```python
from app.utils.certificado_security import invalidar_certificado

invalidar_certificado(
    token="a1b2c3d4...",
    motivo="Certificado comprometido - fraude detectada"
)
```

Isso marca o certificado como inativo. O usuário pode gerar um novo.

### Se um IP estiver atacando

```python
from app.utils.certificado_security import bloquear_ip

bloquear_ip(
    ip_address="192.168.1.1",
    motivo="Ataque de força bruta - 50 tentativas em 1 minuto"
)
```

---

## 📚 Referências de Código

### Arquivo: `app/utils/certificado_security.py`
- Contém todas as funções de segurança
- Gerencia tokens, hashes e auditoria
- Detecta e bloqueia IPs

### Arquivo: `app/handlers/certificado.py`
- Handlers atualizados com segurança
- CertificadoViewHandler
- CertificadoPDFHandler

### Arquivo: `app/handlers/verificar_certificado.py`
- VerificarCertificadoHandler (público)
- VerificarCertificadoAdminHandler (admin)

---

## ✅ Checklist de Implementação

- [ ] Criar tabelas com `criar_tabelas_seguranca()`
- [ ] Adicionar handlers às rotas do `server.py`
- [ ] Testar visualização de certificado
- [ ] Testar download em PDF
- [ ] Testar endpoint público `/verificar-certificado`
- [ ] Testar bloqueio de IP
- [ ] Implementar painel admin (opcional)
- [ ] Documentar para usuários finais

---

## 🔗 Próximos Passos

1. **Implementar 2FA para downloads**
   - Código OTP antes de baixar

2. **Notificações por email**
   - Alertar quando alguém verifica certificado

3. **Watermark dinâmico**
   - Adicionar nome e data no PDF

4. **Integração com blockchain** (futuro)
   - Certificados imutáveis

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique o arquivo `SECURITY.md`
2. Revise os logs em `auditoria_certificados`
3. Consulte a documentação do código

