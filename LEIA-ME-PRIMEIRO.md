# 🛡️ Sistema de Segurança de Certificados - README

## 🎯 O Que É Isso?

Um **sistema completo de segurança** para proteger seus certificados contra:
- ❌ Falsificação de certificados
- ❌ Fraude de candidatos
- ❌ Acesso não autorizado
- ❌ Compartilhamento não rastreável
- ❌ Ataques de força bruta

## ✅ O Que Você Ganha

- ✅ **Token único** para cada certificado
- ✅ **Hash de integridade** que detecta alterações
- ✅ **Auditoria completa** com rastreamento de IP
- ✅ **Bloqueio automático** de IPs suspeitos
- ✅ **Verificação pública** sem necessidade de login
- ✅ **Tudo transparente** para usuários legítimos

## 🚀 COMEÇO RÁPIDO (5 minutos)

### 1. Ler o resumo executivo
```bash
# Leia primeiro (melhor visão geral)
cat RESUMO_SEGURANCA.md
```

### 2. Inicializar o sistema
```bash
# Cria as tabelas de banco de dados
python3 setup_seguranca.py
```

### 3. Adicionar rotas ao seu servidor

No seu `server.py`, adicione:

```python
from app.handlers.verificar_certificado import (
    VerificarCertificadoHandler,
    VerificarCertificadoAdminHandler
)

handlers = [
    # ... suas rotas existentes ...
    (r"/verificar-certificado", VerificarCertificadoHandler),
    (r"/admin/certificado/historico", VerificarCertificadoAdminHandler),
]
```

### 4. Pronto!

Seu sistema agora está protegido. Não precisa fazer mais nada!

## 📚 Documentação

| Documento | Para Quem | Tamanho |
|-----------|-----------|--------|
| **RESUMO_SEGURANCA.md** | Executivos / Gerentes | 5 min |
| **GUIA_CERTIFICADOS_SEGURANCA.md** | Desenvolvedores | 30 min |
| **IMPLEMENTACAO_SEGURANCA_CERTIFICADOS.md** | Técnicos | 20 min |
| **INTEGRACAO_EXEMPLO.py** | Implementadores | Código |

## 📦 Arquivos Criados

```
✅ NOVO: app/utils/certificado_security.py
   └─ Funções: token, hash, auditoria, bloqueio IP
   └─ 267 linhas de código comentado

✅ NOVO: app/handlers/verificar_certificado.py
   └─ Endpoint público: /verificar-certificado
   └─ Admin panel: /admin/certificado/historico

✅ NOVO: GUIA_CERTIFICADOS_SEGURANCA.md
   └─ Documentação técnica completa

✅ NOVO: RESUMO_SEGURANCA.md
   └─ Visão geral e benefícios

✅ NOVO: IMPLEMENTACAO_SEGURANCA_CERTIFICADOS.md
   └─ Exemplos e casos de uso

✅ NOVO: INTEGRACAO_EXEMPLO.py
   └─ Código pronto para integrar

✅ NOVO: setup_seguranca.py
   └─ Script de setup automático

📝 MODIFICADO: app/handlers/certificado.py
   └─ Adicionado: token, auditoria, bloqueio IP
```

## 🔐 Cinco Camadas de Segurança

### 1️⃣ Token Único (32 caracteres)
```
Cada certificado tem um identificador seguro e impossível de adivinhar.
```

### 2️⃣ Hash SHA-256
```
Detecta qualquer alteração nos dados do certificado.
```

### 3️⃣ Auditoria Completa
```
Registra: IP, timestamp, tipo de acesso, quem acessou.
```

### 4️⃣ Bloqueio de IPs Suspeitos
```
5+ tentativas falhas em 5 min = IP bloqueado automaticamente.
```

### 5️⃣ Endpoint Público
```
Terceiros podem validar certificados sem login:
GET /verificar-certificado?token=abc123
```

## 🌐 Como Funciona na Prática

### Usuário Visualiza Certificado
```
1. Usuario faz login
2. Acessa /certificado/2
3. Sistema gera token único (se não existir)
4. Sistema calcula hash
5. Sistema registra acesso em auditoria
6. Usuario vê certificado com ID único
```

### Usuario Compartilha Certificado
```
1. Copia link: https://seusite.com/verificar-certificado?token=abc123
2. Envia para empresa
3. Empresa acessa (sem login)
4. Sistema valida token e hash
5. Sistema retorna dados do certificado
6. Acesso fica registrado com IP da empresa
```

### Admin Invega Fraude
```
1. Acessa /admin/certificado/historico?token=abc123
2. Vê lista de todos que acessaram
3. Vê IPs de cada acesso
4. Pode identificar comportamento suspeito
5. Pode revogar certificado se necessário
```

## 🛑 Exemplos de Proteção

### ❌ Tentativa de Forjar Token
```
Atacante tenta: /verificar-certificado?token=faketoken

Tentativa 1: Token inválido
Tentativa 2: Token inválido
...
Tentativa 5: IP bloqueado automaticamente
```

### ❌ Modificar PDF
```
Usuario modifica arquivo PDF do certificado

Sistema detecta:
- Hash não coincide
- Certificado marcado como inválido
- Auditoria registra incidente
- Admin é alertado
```

### ✅ Validação Legítima
```
Empresa valida candidato com token válido

Sistema permite:
- Token é válido
- Hash coincide
- Dados são retornados
- Acesso registrado
```

## 🧪 Testando o Sistema

### Teste 1: Gerar Token
```python
from app.utils.certificado_security import gerar_token_certificado

token = gerar_token_certificado()
print(token)  # a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### Teste 2: Registrar Certificado
```python
from app.utils.certificado_security import registrar_certificado

cert = registrar_certificado(
    user_id=1,
    modulo=2,
    nota=45,
    data_conclusao="15/02/2026"
)
print(f"Token: {cert['token']}")
```

### Teste 3: Validar Certificado
```python
from app.utils.certificado_security import validar_token_certificado

cert = validar_token_certificado("a1b2c3d4...")
if cert:
    print("✅ Válido")
else:
    print("❌ Inválido")
```

### Teste 4: Endpoint Público
```bash
curl "http://localhost:8888/verificar-certificado?token=a1b2c3d4..."
```

## 📊 Banco de Dados

Três tabelas são criadas automaticamente:

### `certificados`
```
- id: Identificador do certificado
- user_id: Dono do certificado
- modulo: Qual módulo
- nota: Nota obtida
- token: Token único (32 chars)
- hash: Hash SHA-256
- data_geracao: Quando foi gerado
- ativo: 1=válido, 0=revogado
```

### `auditoria_certificados`
```
- id: ID do registro
- user_id: Quem acessou
- token_certificado: Qual certificado
- ip_address: De qual IP
- tipo_acesso: view, download_pdf, verify, denied, etc
- timestamp: Quando
```

### `ips_bloqueados`
```
- id: ID do registro
- ip_address: IP bloqueado (UNIQUE)
- motivo: Por quê foi bloqueado
- data_bloqueio: Quando
- ativo: 1=bloqueado, 0=desbloqueado
```

## ⚙️ Configuração Avançada

### Revogar Certificado
```python
from app.utils.certificado_security import invalidar_certificado

invalidar_certificado("token123", "Fraude detectada")
```

### Ver Histórico
```python
from app.utils.certificado_security import obter_historico_certificado

historico = obter_historico_certificado("token123")
for acesso in historico:
    print(f"{acesso['timestamp']} - {acesso['tipo_acesso']} - {acesso['ip_address']}")
```

### Desbloquear IP
```sql
UPDATE ips_bloqueados SET ativo=0 WHERE ip_address='192.168.1.1'
```

## ❓ Perguntas Frequentes

**P: Preciso fazer algo especial para usuários?**
R: Não! Tudo é transparente. Usuários continuam acessando normalmente.

**P: Os certificados expiram?**
R: Não, a menos que o admin revogue. Você pode implementar expiração futura se desejar.

**P: Posso bloquear um IP manualmente?**
R: Sim! Use `bloquear_ip("192.168.1.1", "Motivo")`

**P: Terceiros podem ver informações sensíveis?**
R: Não! O endpoint público retorna apenas: id, modulo, nota, data_conclusao, ativo

**P: Como reporto fraude?**
R: Admin usa `/admin/certificado/historico` para investigar

## 🚨 Monitoramento

Para detectar ataques, você pode:

```python
import sqlite3

conn = sqlite3.connect("usuarios.db")
cursor = conn.cursor()

# Ver todos os acessos negados
cursor.execute('''
    SELECT ip_address, COUNT(*) as tentativas
    FROM auditoria_certificados
    WHERE tipo_acesso LIKE 'denied%'
    GROUP BY ip_address
    ORDER BY tentativas DESC
''')
```

## 📞 Suporte

Se tiver dúvidas:
1. Leia `RESUMO_SEGURANCA.md`
2. Consulte `GUIA_CERTIFICADOS_SEGURANCA.md`
3. Veja exemplos em `INTEGRACAO_EXEMPLO.py`
4. Revise o código em `app/utils/certificado_security.py`

## 🎓 Próximas Melhorias (Opcionais)

- [ ] 2FA para downloads de PDFs
- [ ] Notificações por email
- [ ] Watermark dinâmico nos PDFs
- [ ] Dashboard de analytics
- [ ] Integração com blockchain
- [ ] Certificados com QR code

## 📄 Licença

Parte do seu sistema de cursos online.

---

**Pronto!** Seu sistema de certificados agora é **seguro, rastreável e à prova de fraude.**

