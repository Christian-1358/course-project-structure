# Sumário do Sistema de Segurança de Certificados

## 🎯 O que foi Implementado

Um sistema **completo e robusto de segurança** para certificados foi criado para prevenir fraude e falsificação. O sistema é transparent para usuários normais, mas oferece proteção máxima.

---

## 📦 Novos Arquivos Criados

### 1. **`app/utils/certificado_security.py`**
Módulo principal com todas as funções de segurança:
- `gerar_token_certificado()` - Cria token de 32 caracteres
- `gerar_hash_certificado()` - Cria hash SHA-256
- `registrar_certificado()` - Salva com token e hash
- `validar_token_certificado()` - Valida um token
- `verificar_integridade_certificado()` - Detecta alterações
- `registrar_acesso_certificado()` - Auditoria
- `detectar_acesso_suspeito()` - Identifica ataques
- `bloquear_ip()` - Bloqueia IPs
- `invalidar_certificado()` - Revoga certificado
- `criar_tabelas_seguranca()` - Inicialização

### 2. **`app/handlers/verificar_certificado.py`**
Handlers para verificação pública:
- `VerificarCertificadoHandler` - Endpoint público
- `VerificarCertificadoAdminHandler` - Para administradores

### 3. **`GUIA_CERTIFICADOS_SEGURANCA.md`**
Documentação completa de como usar e implementar

---

## 🔧 Modificações em Arquivos Existentes

### **`app/handlers/certificado.py`**
Adicionadas:
- Importações das funções de segurança
- Método `get_ip_address()` em ambos handlers
- Validação de IP bloqueado
- Método `_obter_ou_criar_certificado()`
- Registr de acessos em auditoria
- Parâmetro `token` na função `render_html_certificado()`

---

## 🛡️ Camadas de Segurança

### 1️⃣ **Token Único (32 caracteres)**
```
Gerado: secrets.token_hex(16)
Exemplo: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
Armazenado no banco
Impossível adivinhar
```

### 2️⃣ **Hash SHA-256**
```
Dados: user_id|modulo|nota|data
Hash: f1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6...
Se alterado: Hash ≠ Inválida
```

### 3️⃣ **Auditoria Completa**
```
- Cada acesso registrado
- IP do usuário capturado
- Timestamp preciso
- Tipo de acesso (view, download, verify, denied)
```

### 4️⃣ **Bloqueio de IPs**
```
- 5+ tentativas falhas em 5 min = IP bloqueado
- Automático e imediato
- Pode ser desbloqueado manualmente
```

### 5️⃣ **Endpoint Público**
```
GET /verificar-certificado?token=xyz
Retorna: Dados básicos do certificado
Registra: Tentativa de verificação
```

---

## 📊 Tabelas Criadas

### `certificados`
Armazena certificados com proteção:
```sql
- id (PK)
- user_id (FK)
- modulo
- nota
- data_conclusao
- token (UNIQUE) ← Token de segurança
- hash              ← Hash SHA-256
- data_geracao
- ativo (1=válido, 0=revogado)
```

### `auditoria_certificados`
Rastreia todos os acessos:
```sql
- id (PK)
- user_id
- token_certificado
- ip_address        ← IP do cliente
- tipo_acesso       ← view, download, verify, denied, etc
- timestamp         ← Quando aconteceu
```

### `ips_bloqueados`
Bloqueia IPs suspeitos:
```sql
- id (PK)
- ip_address (UNIQUE)
- motivo
- data_bloqueio
- ativo
```

---

## 🚀 Como Usar

### **Inicialização (Uma única vez)**

```python
from app.utils.certificado_security import criar_tabelas_seguranca

# Execute uma vez para criar as tabelas
criar_tabelas_seguranca()
```

### **Registrar um Certificado**

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

### **Validar um Certificado**

```python
from app.utils.certificado_security import validar_token_certificado

cert = validar_token_certificado("a1b2c3d4...")
if cert:
    print(f"Módulo {cert['modulo']}, Nota {cert['nota']}")
else:
    print("Certificado inválido")
```

### **Verificar Integridade**

```python
from app.utils.certificado_security import verificar_integridade_certificado

if verificar_integridade_certificado("a1b2c3d4...", user_id=1):
    print("✅ Certificado válido e não foi alterado")
else:
    print("❌ Certificado foi modificado!")
```

### **Ver Histórico**

```python
from app.utils.certificado_security import obter_historico_certificado

historico = obter_historico_certificado("a1b2c3d4...")
for acesso in historico:
    print(f"{acesso['timestamp']} - {acesso['tipo_acesso']} de {acesso['ip_address']}")
```

### **Revogar um Certificado**

```python
from app.utils.certificado_security import invalidar_certificado

invalidar_certificado(
    token="a1b2c3d4...",
    motivo="Fraude detectada"
)
```

---

## 🌐 Endpoint Público

### Verificar Autenticidade

```bash
GET /verificar-certificado?token=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

Resposta (200):
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

Resposta (404):
{
  "valido": false,
  "erro": "Certificado não encontrado ou inválido"
}

Resposta (403 - IP bloqueado):
{
  "valido": false,
  "erro": "Acesso bloqueado por suspeita de ataque"
}
```

---

## 🔍 Exemplos de Proteção

### **Tentativa 1: Acessar certificado de outro usuário**
```
Usuario A (id=1) tenta: /certificado/view/50
Dono do certificado 50: Usuario B (id=2)

❌ BLOQUEADO
Motivo: Validação de proprietário falha
Auditoria: "denied_acesso_restrito"
```

### **Tentativa 2: Forjar um token**
```
Atacante tenta: /verificar-certificado?token=aaabbbccc...

❌ BLOQUEADO na 1ª tentativa
Se persistir com outros IPs:
- 5+ tentativas em 5 min
- IP bloqueado automaticamente
```

### **Tentativa 3: Usar certificado revogado**
```
Admin revoga certificado de usuário fraudulento
ativo = 0 no banco de dados

❌ BLOQUEADO
Mensagem: "Certificado não encontrado"
```

### **Sucesso: Validar certificado legítimo**
```
Empresa solicita validação de candidato:
GET /verificar-certificado?token=a1b2c3d4...

✅ PERMITIDO
Retorna: Informações do certificado
Auditoria: "verify_publica" registrado
```

---

## 📈 Fluxo de Segurança

```
Usuario A solicita visualizar seu certificado
    ↓
1. Autenticação? (secure cookie)
    ↓ SIM
2. É dono do certificado? (banco de dados)
    ↓ SIM
3. IP está bloqueado? (ips_bloqueados tabela)
    ↓ NÃO
4. Gerar/recuperar token
    ↓
5. Calcular hash de integridade
    ↓
6. Registrar acesso em auditoria
    ↓
7. Exibir certificado com token
    ↓
✅ ACESSO PERMITIDO
```

---

## ✅ Checklist de Implementação

- [x] Criar módulo `certificado_security.py`
- [x] Criar handlers `verificar_certificado.py`
- [x] Atualizar `certificado.py` com segurança
- [x] Tabelas de banco de dados (será criada na 1ª execução)
- [ ] Rodar `criar_tabelas_seguranca()` (NECESSÁRIO - execute uma vez)
- [ ] Testar visualização de certificado
- [ ] Testar download em PDF
- [ ] Testar endpoint público
- [ ] Testar bloqueio de IP
- [ ] Documentar para usuários

---

## 🔗 Próximos Passos (Opcionais)

1. **2FA para downloads**
   - Código OTP antes de baixar PDF

2. **Email notifications**
   - Alertar usuário quando alguém verifica seu certificado

3. **Watermark dinâmico**
   - Adicionar nome do usuário como watermark no PDF

4. **Relatório visual**
   - Dashboard de acessos ao certificado

5. **Integração blockchain**
   - Armazenar hash em blockchain (futuro distante)

---

## 📞 Suporte

Para dúvidas:
1. Leia `GUIA_CERTIFICADOS_SEGURANCA.md`
2. Consulte o código em `app/utils/certificado_security.py`
3. Verifique logs em `auditoria_certificados`

