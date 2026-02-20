import yagmail
import tornado.web
from datetime import datetime

# Configurações Oficiais
EMAIL_USER = "Mudarsenha@gmail.com"
EMAIL_PASS = "smaw uhli vhdi ywff"

def enviar_email_notificacao(tipo, destinatario, dados=None):
    """
    Sistema centralizado de disparos MestreMilhas.
    """
    try:
        yag = yagmail.SMTP(user=EMAIL_USER, password=EMAIL_PASS)
        
        if tipo == "codigo":
            assunto = "🔐 Seu Código de Acesso Premium"
            conteudo = f"""
            <div style="font-family:sans-serif; background:#050505; padding:40px; color:#fff; text-align:center;">
                <div style="max-width:500px; margin:auto; background:#111; padding:30px; border-radius:20px; border:1px solid #d4af37;">
                    <h2 style="color:#d4af37;">Recuperação de Conta</h2>
                    <p>Use o código de verificação abaixo:</p>
                    <div style="font-size:35px; background:#1a1a1a; padding:20px; border-radius:12px; color:#d4af37; margin:20px 0; letter-spacing:8px;">
                        <strong>{dados.get('codigo')}</strong>
                    <div style="font-size:35px; background:#1a1a1a; padding:20px; border-radius:12px; color:#d4af37; margin:20px 0; letter-spacing:8px;">
                        <strong>{dados.get('codigo')}</strong>
                    </div>
                    <p style="color:#666; font-size:12px;">Este código expira em 15 minutos.</p>
                </div>
            </div>
            """
        
        elif tipo == "sucesso":
            assunto = "✅ Segurança: Senha Alterada"
            agora = datetime.now().strftime('%d/%m/%Y às %H:%M')
            conteudo = f"""
            <div style="font-family:sans-serif; background:#f9f9f9; padding:40px; color:#333;">
                <div style="max-width:500px; margin:auto; background:#fff; padding:30px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.1); border-top:6px solid #d4af37;">
                    <h2>Senha Atualizada</h2>
                    <p>A segurança da sua conta foi reforçada com sucesso em <strong>{agora}</strong>.</p>
                </div>
            </div>
            """

        yag.send(to=destinatario, subject=assunto, contents=conteudo)
        return True
    except Exception as e:
        print(f"Erro Crítico de E-mail: {e}")
        return False