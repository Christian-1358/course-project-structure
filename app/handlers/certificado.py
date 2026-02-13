import os
import sqlite3
import tornado.ioloop
import tornado.web
from datetime import datetime

try:
    import weasyprint
    from weasyprint import HTML, CSS
    # FontConfiguration location changed across versions; try common locations
    try:
        from weasyprint import FontConfiguration
    except Exception:
        try:
            from weasyprint.document import FontConfiguration
        except Exception:
            try:
                from weasyprint.text.fonts import FontConfiguration
            except Exception:
                FontConfiguration = None
except ImportError:
    HTML = None
    CSS = None
    FontConfiguration = None

from app.utils.certificado_security import (
    registrar_certificado,
    registrar_acesso_certificado,
    validar_token_certificado,
    ip_esta_bloqueado,
    detectar_acesso_suspeito,
    bloquear_ip
)
from app.utils.security import set_flow_allowed_if_referer, consume_flow_allowed
import asyncio
try:
    from pyppeteer import launch as pyppeteer_launch
except Exception:
    pyppeteer_launch = None

# ================== CONFIG ==================
# Usa a conexão centralizada (aponta para usuarios.db na raiz do projeto)
from app.utils.admin_tools import conectar

# Definições dos módulos com ementas
MODULOS_INFO = {
    1: {"titulo": "Módulo 1", "ementa": "Fundamentos de Milhas Aéreas", "questoes": 10},
    2: {"titulo": "Módulo 2", "ementa": "Estratégias de Acúmulo", "questoes": 10},
    3: {"titulo": "Módulo 3", "ementa": "Resgate e Transferências", "questoes": 10},
    4: {"titulo": "Módulo 4", "ementa": "Cartões de Crédito Premium", "questoes": 10},
    5: {"titulo": "Módulo 5", "ementa": "Otimização de Pontos", "questoes": 10},
    6: {"titulo": "Prova Final", "ementa": "Mestre das Milhas - Avaliação Completa", "questoes": 50},
}

# usa `conectar()` importada de `app.utils.admin_tools`

def obter_dados_certificado(user_id, modulo):
    """
    Obtém dados do usuário e da prova para gerar certificado.
    """
    conn = conectar()
    
    # Obter dados do usuário
    user = conn.execute("SELECT username, email FROM users WHERE id = ?", (user_id,)).fetchone()
    
    # Obter resultado da prova
    resultado = conn.execute(
        "SELECT nota, data FROM provas_resultado WHERE user_id = ? AND modulo = ?",
        (user_id, modulo)
    ).fetchone()
    
    conn.close()
    
    if not user or not resultado:
        return None
    
    return {
        "nome": user["username"].upper(),
        "email": user["email"],
        "nota": resultado["nota"],
        "data": resultado["data"],
        "modulo": modulo
    }

def render_html_certificado(nome, email, nota, data_conclusao, modulo, is_pdf=False, token=None):
    """
    Renderiza HTML do certificado com dados reais.
    """
    mod_info = MODULOS_INFO.get(int(modulo), {})
    titulo_mod = mod_info.get("titulo", f"Módulo {modulo}")
    ementa = mod_info.get("ementa", "Curso Online")
    questoes = mod_info.get("questoes", 10)
    
    # Formatar data
    try:
        if data_conclusao:
            data_obj = datetime.strptime(data_conclusao, "%d/%m/%Y %H:%M:%S")
            data_formatada = data_obj.strftime("%d de %B de %Y").replace("January", "janeiro").replace("February", "fevereiro").replace("March", "março").replace("April", "abril").replace("May", "maio").replace("June", "junho").replace("July", "julho").replace("August", "agosto").replace("September", "setembro").replace("October", "outubro").replace("November", "novembro").replace("December", "dezembro")
        else:
            data_formatada = datetime.now().strftime("%d de %B de %Y").replace("January", "janeiro").replace("February", "fevereiro").replace("March", "março").replace("April", "abril").replace("May", "maio").replace("June", "junho").replace("July", "julho").replace("August", "agosto").replace("September", "setembro").replace("October", "outubro").replace("November", "novembro").replace("December", "dezembro")
    except:
        data_formatada = datetime.now().strftime("%d/%m/%Y")
    
    # Botão só aparece na visualização do navegador (HTML)
    btn_html = f'''
    <div class="acoes" style="text-align:center; margin-top:20px;">
        <a class="btn" href="/certificado/pdf/{modulo}" 
           style="background:#d4b038; color:#000; padding:15px 25px; text-decoration:none; font-weight:bold; border-radius:5px;">
           ⬇ BAIXAR CERTIFICADO EM PDF
        </a>
    </div>
    ''' if not is_pdf else ''

    zoom_style = "zoom: 0.75;" if is_pdf else ""
    
    # Token de verificação (mostrado apenas se disponível)
    token_display = f"""
    <div class="codigo">ID Único: {token[:8] if token else ''}</div>
    """ if token and not is_pdf else ""

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <style>
        @page {{ size: A4 landscape; margin: 0; }}
        body {{ margin: 0; padding: 0; background: {('#fff' if is_pdf else '#000')}; font-family: "DejaVu Serif", Georgia, serif; }}
        .viewer {{ min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; {zoom_style}; padding: 20px; }}
        .certificado {{ 
            width: 1200px; height: 800px; background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
            border: 25px solid #d4b038; padding: 0; position: relative; box-sizing: border-box;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }}
        .inner {{ 
            width: 100%; height: 100%; border: 3px solid #d4b038; 
            padding: 60px 80px; text-align: center; color: #e8e8e8; box-sizing: border-box;
            display: flex; flex-direction: column; justify-content: space-between;
        }}
        .header {{ margin-bottom: 30px; }}
        .logo {{ letter-spacing: 8px; font-size: 24px; color: #d4b038; font-weight: bold; margin-bottom: 20px; }}
        .titulo {{ font-size: 56px; color: #d4b038; margin: 20px 0; font-weight: bold; letter-spacing: 2px; }}
        .subtitulo {{ font-size: 16px; color: #aaa; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 30px; }}
        .content {{ flex-grow: 1; display: flex; flex-direction: column; justify-content: center; }}
        .nome {{ font-size: 42px; font-weight: bold; color: #fff; margin: 30px 0 20px 0; }}
        .nome-underline {{ border-bottom: 3px solid #d4b038; padding-bottom: 10px; display: inline-block; min-width: 400px; }}
        .texto {{ font-size: 18px; color: #ddd; line-height: 1.8; margin: 20px 0; }}
        .modulo-info {{ font-size: 16px; color: #aaa; margin: 15px 0; }}
        .nota-info {{ font-size: 16px; color: #d4b038; font-weight: bold; margin: 15px 0; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #d4b038; }}
        .data {{ font-size: 14px; color: #888; letter-spacing: 1px; }}
        .codigo {{ font-size: 11px; color: #666; margin-top: 10px; font-family: monospace; }}
    </style>
</head>
        try:
            print(f"[cert_pdf_chrome] Rendering URL: {url} for user_id={user_id}")
            # debug: show if cookie exists in incoming request
            try:
                cookie_obj = self.request.cookies.get('user_id')
                print(f"[cert_pdf_chrome] incoming cookie user_id present: {bool(cookie_obj)}")
            except Exception:
                pass
            # Run the async render in Tornado's current IOLoop to avoid nested event loop
            pdf_bytes = tornado.ioloop.IOLoop.current().run_sync(_render)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[cert_pdf_chrome] exception: {e}")
            self.set_status(500)
            self.write(f'Erro ao renderizar PDF via Chromium: {e}')
            return
                    </div>
                    <div class="modulo-info" style="font-size: 20px; color: #d4b038; font-weight: bold;">
                        {titulo_mod}
                    </div>
                    <div class="texto">
                        {ementa}
                    </div>
                    <div class="nota-info">
                        Nota Final: <strong>{int(nota)}/{questoes} pontos</strong>
                    </div>
                </div>
                
                <div class="footer">
                    <div class="data">Concluído em: {data_formatada}</div>
                    {token_display}
                </div>
            </div>
        </div>
        {btn_html}
    </div>
</body>
</html>
"""


def obter_ou_criar_certificado(user_id, modulo, nota, data_conclusao):
    """
    Helper compartilhado: obtém certificado existente ou cria um novo.
    Retorna dict com 'id' e 'token' ou None em caso de erro.
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, token FROM certificados
        WHERE user_id = ? AND modulo = ?
        LIMIT 1
        """,
        (user_id, modulo)
    )
    existente = cursor.fetchone()

    if existente:
        conn.close()
        return {"id": existente[0], "token": existente[1]}

    try:
        cert_info = registrar_certificado(user_id, modulo, nota, data_conclusao)
        conn.close()
        return cert_info
    except Exception as e:
        conn.close()
        print(f"Erro ao criar certificado: {e}")
        return None


class CertificadoViewHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    def get_ip_address(self):
        """Obtém o IP real do cliente (considerando proxies)"""
        ip = self.request.headers.get("X-Forwarded-For")
        if ip:
            return ip.split(",")[0].strip()
        return self.request.remote_ip

    @tornado.web.authenticated
    def get(self, modulo_id):

        user_id = self.current_user
        ip_address = self.get_ip_address()

        # Central verify: autenticado, pago e fluxo válido para certificado PDF
        try:
            mod_check = int(modulo_id)
        except Exception:
            mod_check = None

        from app.utils.security import verify_flow_and_payment
        if mod_check and not verify_flow_and_payment(self, 'certificado', mod_check):
            registrar_acesso_certificado(user_id, None, ip_address, "denied_direct_pdf")
            return
        # Central verify: autenticado, pago e fluxo válido para certificado
        try:
            mod_check = int(modulo_id)
        except Exception:
            mod_check = None

        from app.utils.security import verify_flow_and_payment
        if mod_check and not verify_flow_and_payment(self, 'certificado', mod_check):
            registrar_acesso_certificado(user_id, None, ip_address, "denied_direct_url")
            return

        # 🔒 Verificar se IP está bloqueado
        if ip_esta_bloqueado(ip_address):
            self.set_status(403)
            self.write("<h1>Acesso Negado (403)</h1><p>Seu IP foi bloqueado por atividade suspeita.</p>")
            return

        # 🔒 Validar módulo permitido
        try:
            modulo = int(modulo_id)
        except:
            self.set_status(400)
            self.write("Módulo inválido.")
            return

        if modulo not in MODULOS_INFO:
            self.set_status(404)
            self.write("Certificado inexistente.")
            return

        # 🔒 Verificar se usuário está ativo e pagou
        conn = conectar()
        user = conn.execute(
            "SELECT pago, ativo FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not user or user["pago"] != 1 or user["ativo"] != 1:
            conn.close()
            self.set_status(403)
            self.write("<h1>Acesso Negado (403)</h1><p>Conta inativa ou pagamento pendente.</p>")
            registrar_acesso_certificado(user_id, None, ip_address, "denied_acesso_restrito")
            return

        # 🔒 Buscar resultado da prova (somente do próprio usuário)
        resultado = conn.execute(
            """SELECT nota, data, aprovado 
               FROM provas_resultado 
               WHERE user_id = ? AND modulo = ?""",
            (user_id, modulo)
        ).fetchone()

        conn.close()

        if not resultado or resultado["aprovado"] != 1:
            self.set_status(403)
            self.write("<h1>Acesso Negado (403)</h1><p>Você ainda não foi aprovado neste módulo.</p>")
            registrar_acesso_certificado(user_id, None, ip_address, "denied_nao_aprovado")
            return

        # ✅ Registrar ou obter token do certificado
        cert_info = obter_ou_criar_certificado(user_id, modulo, resultado["nota"], resultado["data"])
        
        if not cert_info:
            self.set_status(500)
            self.write("<h1>Erro ao processar certificado</h1>")
            return

        token = cert_info["token"]

        # ✅ Registrar acesso bem-sucedido
        registrar_acesso_certificado(user_id, token, ip_address, "view")
        # Renderizar usando templates existentes para manter o layout
        nome_aluno = self.get_user_nome(user_id)
        mod_info = MODULOS_INFO.get(modulo, {})
        ementa = mod_info.get("ementa", "Curso Online")

        # preparar datas (sqlite3.Row -> usar indexação)
        inicio = resultado["data"] if resultado["data"] else datetime.now().strftime("%d/%m/%Y")
        fim = inicio

        if modulo == 6:
            # prova final -> usar template final
            try:
                self.render("certificado_final.html", nome=nome_aluno, data=inicio, modulo=modulo, ementa=ementa, inicio=inicio, fim=fim)
                return
            except Exception:
                # fallback para HTML gerado quando template não estiver disponível
                html = render_html_certificado(nome_aluno, "", resultado["nota"], resultado["data"], modulo, is_pdf=False, token=token)
                self.write(html)
                return

        # módulos normais -> usa template certificado.html
        try:
            self.render("certificado.html", nome=nome_aluno, inicio=inicio, fim=fim, modulo=modulo, ementa=ementa)
        except Exception:
            # fallback em caso de erro no template
            html = render_html_certificado(nome_aluno, "", resultado["nota"], resultado["data"], modulo, is_pdf=False, token=token)
            self.write(html)
        return

    # nota: agora usamos a função module-level `obter_ou_criar_certificado`

    def get_user_nome(self, user_id):
        conn = conectar()
        user = conn.execute(
            "SELECT username FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        conn.close()
        return user["username"].upper()

class CertificadoPDFHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    def get_ip_address(self):
        """Obtém o IP real do cliente (considerando proxies)"""
        ip = self.request.headers.get("X-Forwarded-For")
        if ip:
            return ip.split(",")[0].strip()
        return self.request.remote_ip

    @tornado.web.authenticated
    def get(self, modulo_id):

        user_id = self.current_user
        ip_address = self.get_ip_address()

        # 🔒 Verificar se IP está bloqueado
        if ip_esta_bloqueado(ip_address):
            self.set_status(403)
            self.write("Acesso bloqueado por atividade suspeita.")
            return

        try:
            modulo = int(modulo_id)
        except:
            self.set_status(400)
            self.write("Módulo inválido.")
            return

        if modulo not in MODULOS_INFO:
            self.set_status(404)
            self.write("Certificado inexistente.")
            return

        if not HTML:
            self.set_status(500)
            self.write("WeasyPrint não instalado.")
            return

        conn = conectar()

        user = conn.execute(
            "SELECT username, pago, ativo FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not user or user["pago"] != 1 or user["ativo"] != 1:
            conn.close()
            self.set_status(403)
            self.write("Acesso negado.")
            return

        resultado = conn.execute(
            """SELECT nota, data, aprovado 
               FROM provas_resultado 
               WHERE user_id = ? AND modulo = ?""",
            (user_id, modulo)
        ).fetchone()

        # Para o certificado final (modulo 6) permitimos geração mesmo se não existir linha em provas_resultado,
        # desde que o usuário tenha `certificado_fin = 1` ou `nota_final >= 7`.
        if modulo == 6:
            user_row = conn.execute("SELECT nota_final, certificado_fin, inicio_curso FROM users WHERE id = ?", (user_id,)).fetchone()
            # sqlite3.Row não tem .get(), usar indexação segura
            certificado_fin_val = None
            nota_final_val = None
            inicio_curso_val = None
            if user_row:
                try:
                    certificado_fin_val = user_row['certificado_fin']
                except Exception:
                    certificado_fin_val = None
                try:
                    nota_final_val = user_row['nota_final']
                except Exception:
                    nota_final_val = None
                try:
                    inicio_curso_val = user_row['inicio_curso']
                except Exception:
                    inicio_curso_val = None

            if user_row and ((certificado_fin_val == 1) or (nota_final_val is not None and int(nota_final_val) >= 7)):
                # montar resultado fake a partir dos dados do usuário
                fake_nota = nota_final_val if nota_final_val is not None else 0
                fake_data = inicio_curso_val or datetime.now().strftime('%d/%m/%Y')
                resultado = {'nota': fake_nota, 'data': fake_data, 'aprovado': 1}
            else:
                resultado = conn.execute(
                    """SELECT nota, data, aprovado 
                       FROM provas_resultado 
                       WHERE user_id = ? AND modulo = ?""",
                    (user_id, modulo)
                ).fetchone()
        else:
            resultado = conn.execute(
                """SELECT nota, data, aprovado 
                   FROM provas_resultado 
                   WHERE user_id = ? AND modulo = ?""",
                (user_id, modulo)
            ).fetchone()

        conn.close()

        if not resultado or (isinstance(resultado, dict) and resultado.get('aprovado') != 1) or (not isinstance(resultado, dict) and resultado["aprovado"] != 1):
            self.set_status(403)
            self.write("Você não foi aprovado neste módulo.")
            registrar_acesso_certificado(user_id, None, ip_address, "denied_pdf_nao_aprovado")
            return

        # ✅ Obter ou criar certificado com token
        cert_info = obter_ou_criar_certificado(user_id, modulo, resultado["nota"], resultado["data"])
        
        if not cert_info:
            self.set_status(500)
            self.write("Erro ao processar certificado.")
            return

        token = cert_info["token"]

        html_content = render_html_certificado(
            nome=user["username"].upper(),
            email="",
            nota=resultado["nota"],
            data_conclusao=resultado["data"],
            modulo=modulo,
            is_pdf=True,
            token=token
        )

        # Melhor geração de PDF: para o certificado final usamos HTML totalmente inline
        try:
            font_config = FontConfiguration() if FontConfiguration else None
            base_url = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
            if modulo == 6:
                # Prefer renderizar o template Tornado para que o PDF reproduza fielmente o HTML visto no navegador
                try:
                    rendered = self.render_string("certificado_final.html", nome=user["username"].upper(), data=resultado["data"], modulo=modulo, ementa=MODULOS_INFO.get(modulo, {}).get("ementa", ""), inicio=resultado["data"], fim=resultado["data"]) 
                except Exception:
                    # fallback para HTML gerado programaticamente
                    rendered = html_content
            else:
                # para módulos normais, tentar renderizar o template (pode usar estilos externos)
                try:
                    rendered = self.render_string("certificado.html", nome=user["username"].upper(), inicio=resultado["data"], fim=resultado["data"], modulo=modulo, ementa=MODULOS_INFO.get(modulo, {}).get("ementa", ""))
                except Exception:
                    rendered = html_content

            if HTML is None:
                raise RuntimeError('WeasyPrint não disponível')

            page_css = CSS(string='@page { size: A4 landscape; margin: 0 }') if CSS else None
            if page_css and font_config:
                pdf_bytes = HTML(string=rendered, base_url=base_url).write_pdf(stylesheets=[page_css], font_config=font_config, presentational_hints=True)
            elif page_css:
                pdf_bytes = HTML(string=rendered, base_url=base_url).write_pdf(stylesheets=[page_css])
            else:
                pdf_bytes = HTML(string=rendered, base_url=base_url).write_pdf()
        except Exception as e:
            print(f"Erro ao gerar PDF do certificado: {e}")
            try:
                pdf_bytes = HTML(string=html_content).write_pdf()
            except Exception as e2:
                print(f"Fallback PDF também falhou: {e2}")
                self.set_status(500)
                self.write("Erro ao gerar PDF do certificado.")
                return

        # ✅ Registrar download bem-sucedido
        registrar_acesso_certificado(user_id, token, ip_address, "download_pdf")

        self.set_header("Content-Type", "application/pdf")
        self.set_header(
            "Content-Disposition",
            f"attachment; filename=Certificado_Modulo_{modulo}.pdf"
        )
        self.write(pdf_bytes)


class CertificadoPDFChromeHandler(tornado.web.RequestHandler):
    """Gera PDF usando headless Chromium (pyppeteer) para máxima fidelidade visual.
    URL: /certificado/pdf_chrome/<modulo>
    """
    def get_current_user(self):
        uid = self.get_secure_cookie("user_id")
        return int(uid.decode()) if uid else None

    @tornado.web.authenticated
    def get(self, modulo_id):
        if pyppeteer_launch is None:
            self.set_status(500)
            self.write('pyppeteer não instalado. Instale com: pip install pyppeteer')
            return

        user_id = self.get_current_user()
        # basic checks (reuse CertificadoPDFHandler logic minimally)
        try:
            modulo = int(modulo_id)
        except:
            self.set_status(400); self.write('Módulo inválido'); return

        # build URL to the certificate HTML view so Chromium renders same page
        proto = 'http'
        host = self.request.host
        url = f"{proto}://{host}/certificado/{modulo}"

        async def _render():
            browser = await pyppeteer_launch(headless=True, args=['--no-sandbox'])
            page = await browser.newPage()
            await page.setViewport({'width': 1200, 'height': 800})
            # Forward the user's secure cookie so the headless browser is authenticated
            try:
                cookie_obj = self.request.cookies.get('user_id')
                if cookie_obj:
                    cookie_value = cookie_obj.value
                    domain = host.split(':')[0]
                    await page.setCookie({
                        'name': 'user_id',
                        'value': cookie_value,
                        'domain': domain,
                        'path': '/',
                        'httpOnly': False,
                        'secure': False,
                    })
            except Exception:
                pass

            await page.goto(url, {'waitUntil': 'networkidle0'})
            pdf_bytes = await page.pdf({
                'format': 'A4',
                'landscape': True,
                'printBackground': True,
                'scale': 1.0,
                'preferCSSPageSize': True
            })
            await browser.close()
            return pdf_bytes

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            print(f"[cert_pdf_chrome] Rendering URL: {url} for user_id={user_id}")
            # debug: show if cookie exists in incoming request
            try:
                cookie_obj = self.request.cookies.get('user_id')
                print(f"[cert_pdf_chrome] incoming cookie user_id present: {bool(cookie_obj)}")
            except Exception:
                pass
            pdf_bytes = loop.run_until_complete(_render())
            loop.close()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[cert_pdf_chrome] exception: {e}")
            self.set_status(500)
            self.write(f'Erro ao renderizar PDF via Chromium: {e}')
            return

        self.set_header('Content-Type', 'application/pdf')
        self.set_header('Content-Disposition', f'attachment; filename=Certificado_Modulo_{modulo}.pdf')
        self.write(pdf_bytes)

    # usa `obter_ou_criar_certificado` (definida no módulo)


