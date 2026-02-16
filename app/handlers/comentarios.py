import json
import sqlite3
import os
import tornado.web

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")


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

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            c.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_id TEXT,
                    content TEXT,
                    created_at TEXT
                )
            """)

            c.execute(
                "INSERT INTO comments (lesson_id, content, created_at) VALUES (?, ?, datetime('now'))",
                (lesson_id, content)
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

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            SELECT content, created_at 
            FROM comments 
            WHERE lesson_id = ?
            ORDER BY id DESC
        """, (lesson_id,))

        rows = c.fetchall()
        conn.close()

        self.write(json.dumps([
            {"content": r[0], "created_at": r[1]}
            for r in rows
        ]))
