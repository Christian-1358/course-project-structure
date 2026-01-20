

import yagmail

# SUBSTITUA PELOS SEUS DADOS
USER = "chrstnposso@gmail.com"
PASS = "cjwjerujeejdj"

try:
    print("Tentando conectar ao Gmail...")
    yag = yagmail.SMTP(USER, PASS)
    yag.send(to=USER, subject="Teste", contents="Se você recebeu isso, funciona!")
    print("✅ SUCESSO! O e-mail foi enviado.")
except Exception as e:
    print("❌ ERRO DETALHADO:")
    print(e)

