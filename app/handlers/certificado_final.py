from weasyprint import HTML, CSS
from io import BytesIO

class CertificadoFinalHandler(tornado.web.RequestHandler):
    @tornado.web.authenticated
    def get(self):
        user_id = int(self.get_secure_cookie("user_id").decode())
        download = self.get_argument("download", None)

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT COALESCE(nome, username) as nome, inicio_curso FROM users WHERE id = ?", (user_id,))
            user = c.fetchone()

        if not user: self.redirect("/login")

        nome = user['nome']
        data_fim = datetime.now().strftime("%d/%m/%Y")
        
        # Conteúdo Consolidado
        ementa_completa = "Formação completa: Fundamentos, Cartões e Benefícios, Acúmulo Estratégico, Emissões Internacionais e Gestão de Milhas como Negócio."

        html_content = self.render_string("certificado_final.html", nome=nome, ementa=ementa_completa, data=data_fim).decode('utf-8')

        # CSS Profissional para Certificado de Formação
        pdf_css = CSS(string="""
            @page { size: A4 landscape; margin: 0; }
            body { background: #000; margin: 0; font-family: sans-serif; }
            .cert-canvas {
                width: 297mm; height: 210mm; display: table;
                background: #000; border: 15mm solid #d4af37; box-sizing: border-box;
            }
            .inner-wrapper { display: table-cell; vertical-align: middle; text-align: center; }
            .inner-border { 
                display: inline-block; width: 250mm; height: 170mm; 
                border: 2pt solid #c9a63a; padding: 40pt; box-sizing: border-box; 
            }
            h1 { font-size: 55pt; color: #d4af37; text-transform: uppercase; margin: 0; }
            .title-expert { font-size: 20pt; color: #fff; letter-spacing: 10pt; margin-bottom: 20pt; }
            .student-name { font-size: 45pt; color: #fff; font-weight: bold; border-bottom: 3pt solid #d4af37; display: inline-block; margin: 20pt 0; }
            .desc { font-size: 16pt; color: #ccc; width: 80%; margin: 0 auto; line-height: 1.6; }
            .footer { margin-top: 40pt; display: table; width: 100%; }
            .sign { display: table-cell; border-top: 1pt solid #444; color: #777; font-size: 9pt; padding-top: 10pt; }
        """)

        pdf_file = BytesIO()
        HTML(string=html_content).write_pdf(pdf_file, stylesheets=[pdf_css])
        pdf_file.seek(0)

        self.set_header("Content-Type", "application/pdf")
        self.set_header("Content-Disposition", f'attachment; filename="ESPECIALISTA_{nome}.pdf"')
        self.write(pdf_file.read())