import json
import sqlite3
import os
import tornado.web

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# keep comments in own database file separated from user records
DB_PATH = os.path.join(BASE_DIR, "comments.db")
USERS_DB = os.path.join(BASE_DIR, "usuarios.db")

# migration: if users.db still contains an old comments table and the new DB is empty, copy rows
try:
    if os.path.exists(USERS_DB):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # ensure target table exists so we can count
        c.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id TEXT,
                user_id INTEGER,
                content TEXT,
                parent_id INTEGER,
                created_at TEXT
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_comments_lesson ON comments(lesson_id)")
        # count target rows
        c.execute("SELECT count(*) FROM comments")
        target_count = c.fetchone()[0]
        # attach old database and see if there is an old table
        c.execute("ATTACH ? AS old", (USERS_DB,))
        c.execute("SELECT count(*) FROM old.sqlite_master WHERE type='table' AND name='comments'")
        if c.fetchone()[0] > 0 and target_count == 0:
            # copy everything
            c.execute(
                "INSERT INTO comments (lesson_id,user_id,content,parent_id,created_at) SELECT lesson_id,user_id,content,parent_id,created_at FROM old.comments"
            )
        c.execute("DETACH old")
        conn.commit()
        conn.close()
except Exception:
    pass


class CommentHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    def post(self):
        try:
            data = json.loads(self.request.body)
            lesson_id = data.get("lesson_id")
            content = data.get("content")

            if not lesson_id or not content:
                self.set_status(400)
                self.write(json.dumps({"error": "Dados inválidos"}))
                return

            # cada comentário é associado a uma "lesson_id" (vídeo/aula)
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            # criar tabela caso não exista e garantir colunas necessárias
            c.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_id TEXT,
                    user_id INTEGER,
                    content TEXT,
                    parent_id INTEGER,
                    created_at TEXT
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_comments_lesson ON comments(lesson_id)")
            # caso a tabela já existisse antes, reafirmamos presença de colunas
            cols = [r[1] for r in c.execute("PRAGMA table_info(comments)")]  # lista de nomes de coluna
            if 'user_id' not in cols:
                try:
                    c.execute("ALTER TABLE comments ADD COLUMN user_id INTEGER")
                except Exception:
                    pass
            if 'parent_id' not in cols:
                try:
                    c.execute("ALTER TABLE comments ADD COLUMN parent_id INTEGER")
                except Exception:
                    pass

            # o usuário precisa estar logado (não exigimos pagamento para comentar)
            user_cookie = self.get_secure_cookie("user_id")
            if not user_cookie:
                self.set_status(401)
                self.write(json.dumps({"error": "login_required"}))
                return
            try:
                user_id = int(user_cookie.decode())
            except Exception:
                self.set_status(401)
                self.write(json.dumps({"error": "login_required"}))
                return
            # opcional: se quiser forçar pago, descomente abaixo
            # if not usuario_pagou(user_id):
            #     self.set_status(403)
            #     self.write(json.dumps({"error": "payment_required"}))
            #     return

            # parent_id opcional para respostas
            parent = data.get("parent_id")
            if parent:
                c.execute(
                    "INSERT INTO comments (lesson_id, user_id, content, parent_id, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                    (lesson_id, user_id, content, parent)
                )
            else:
                c.execute(
                    "INSERT INTO comments (lesson_id, user_id, content, created_at) VALUES (?, ?, ?, datetime('now'))",
                    (lesson_id, user_id, content)
                )

            conn.commit()
            conn.close()

            self.write(json.dumps({"status": "ok"}))

        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}))

    def get(self):
        lesson_id = self.get_argument("lesson_id", None)

        if not lesson_id:
            self.write(json.dumps([]))
            return

        # abrimos banco dedicado a comentários
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # anexa banco de usuários para poder recuperar nome/foto
        try:
            c.execute("ATTACH ? AS udb", (USERS_DB,))
        except Exception:
            pass

        # buscamos comentários e respostas, depois organizamos em árvore
        c.execute("""
            SELECT c.id, c.content, c.parent_id, c.created_at,
                   c.user_id, udb.users.username, udb.users.photo
            FROM comments c
            LEFT JOIN udb.users ON udb.users.id = c.user_id
            WHERE c.lesson_id = ?
            ORDER BY c.id DESC
        """, (lesson_id,))

        rows = c.fetchall()
        try:
            c.execute("DETACH udb")
        except Exception:
            pass
        conn.close()

        # montar árvore simples: mapa id -> comment dict
        items = []
        by_id = {}
        for r in rows:
            cid, content, parent, created, uid, username, photo = r
            node = {"id": cid, "content": content, "created_at": created,
                    "user_id": uid, "username": username, "photo": photo,
                    "replies": []}
            by_id[cid] = node
            if parent:
                # será anexado depois
                pass
            else:
                items.append(node)
        # agora inserimos replies
        for r in rows:
            cid, content, parent, created, uid, username, photo = r
            if parent and parent in by_id:
                by_id[parent]["replies"].append(by_id[cid])
        self.write(json.dumps(items))
