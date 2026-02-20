import tornado.web
from datetime import datetime
from app.handlers.base import BaseHandler, require_auth
from sqlite import conectar
# ==========================================
# CRIAR COMENTÁRIO
# ==========================================
class CriarComentarioHandler(BaseHandler):
    @require_auth
    def post(self):
        user_id = self.current_user["id"]
        conteudo = self.get_argument("conteudo")

        if not conteudo.strip():
            self.write({"status": "erro", "msg": "Comentário vazio"})
            return

        conn = conectar()
        c = conn.cursor()

        c.execute("""
            INSERT INTO comentarios (user_id, conteudo, criado_em)
            VALUES (?, ?, ?)
        """, (
            user_id,
            conteudo.strip(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        self.write({"status": "ok"})


# ==========================================
# LISTAR COMENTÁRIOS
# ==========================================
class ListarComentariosHandler(BaseHandler):
    def get(self):
        conn = conectar()
        c = conn.cursor()

        c.execute("""
            SELECT 
                c.id,
                c.conteudo,
                c.criado_em,
                u.username,

                (SELECT COUNT(*) FROM comentario_reacoes 
                 WHERE comentario_id = c.id AND tipo = 'like') as likes,

                (SELECT COUNT(*) FROM comentario_reacoes 
                 WHERE comentario_id = c.id AND tipo = 'dislike') as dislikes

            FROM comentarios c
            JOIN users u ON u.id = c.user_id
            ORDER BY c.id DESC
        """)

        comentarios = [dict(row) for row in c.fetchall()]

        conn.close()
        self.write({"comentarios": comentarios})


# ==========================================
# LIKE / DESLIKE (INTELIGENTE)
class ReagirComentarioHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self):

        comentario_id = self.get_argument("comentario_id")
        tipo = self.get_argument("tipo")
        usuario_id = self.current_user

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM comentario_reacoes
            WHERE comentario_id=? AND usuario_id=?
        """, (comentario_id, usuario_id))

        if cursor.fetchone():
            self.set_status(400)
            self.write({"erro": "Você já reagiu"})
            conn.close()
            return

        cursor.execute("""
            INSERT INTO comentario_reacoes (comentario_id, usuario_id, tipo)
            VALUES (?, ?, ?)
        """, (comentario_id, usuario_id, tipo))

        conn.commit()
        conn.close()

        self.write({"ok": True})

# ==========================================
# DENUNCIAR USUÁRIO
# ==========================================
class DenunciarUsuarioHandler(BaseHandler):
    @require_auth
    def post(self):
        denunciante_id = self.current_user["id"]
        denunciado_id = self.get_argument("denunciado_id")
        motivo = self.get_argument("motivo", "")

        if denunciante_id == int(denunciado_id):
            self.write({"status": "erro", "msg": "Você não pode denunciar a si mesmo"})
            return

        conn = conectar()
        c = conn.cursor()

        c.execute("""
            INSERT INTO denuncias 
            (denunciante_id, denunciado_id, motivo, criado_em)
            VALUES (?, ?, ?, ?)
        """, (
            denunciante_id,
            denunciado_id,
            motivo.strip(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        self.write({"status": "ok"})