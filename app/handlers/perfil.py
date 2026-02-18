import os
import tornado.web
from app.handlers.login import hash_senha
from app.utils.pagamento_utils import conectar
from app.handlers.base import BaseHandler, require_auth


class PerfilHandler(BaseHandler):

    # ===============================
    # GARANTE COLUNAS NO BANCO
    # ===============================
    def ensure_profile_columns(self):
        conn = conectar()
        c = conn.cursor()
        cols = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
        changed = False

        if "bio" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN bio TEXT")
            changed = True

        if "photo" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN photo TEXT")
            changed = True

        if changed:
            conn.commit()

        conn.close()


    # ===============================
    # GET
    # ===============================
    @require_auth
    def get(self):
        user_id = self.get_current_user()
        self.ensure_profile_columns()

        conn = conectar()
        c = conn.cursor()
        c.execute("SELECT username, email, bio, photo FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            self.redirect("/login")
            return

        self.render(
            "perfil.html",
            username=row["username"],
            email=row["email"],
            bio=row["bio"] or "",
            photo=row["photo"] or "",
            mensagem=None,
            erro=None
        )


    # ===============================
    # POST
    # ===============================
    @require_auth
    def post(self):
        user_id = self.get_current_user()
        action = self.get_argument("action", "")

        conn = conectar()
        c = conn.cursor()
        c.execute("SELECT username, email, password, bio, photo FROM users WHERE id=?", (user_id,))
        row = c.fetchone()

        if not row:
            conn.close()
            self.redirect("/login")
            return

        username = row["username"]
        email = row["email"]
        current_hash = row["password"]
        current_photo = row["photo"]


        # ==================================================
        # REMOVER FOTO
        # ==================================================
        if action == "remove_photo":

            if current_photo:
                file_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "app", current_photo.replace("/static/", "static/")
                )
                if os.path.exists(file_path):
                    os.remove(file_path)

            c.execute("UPDATE users SET photo=NULL WHERE id=?", (user_id,))
            conn.commit()
            conn.close()

            self.write({"status": "ok"})
            return


        # ==================================================
        # EXCLUIR CONTA
        # ==================================================
        if action == "delete_account":

            if current_photo:
                file_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "app", current_photo.replace("/static/", "static/")
                )
                if os.path.exists(file_path):
                    os.remove(file_path)

            c.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()
            conn.close()

            self.clear_cookie("user")
            self.write({"status": "deleted"})
            return


        # ==================================================
        # ALTERAR SENHA
        # ==================================================
        if action == "change_password":

            old = self.get_argument("old", "").strip()
            new = self.get_argument("new", "").strip()
            confirm = self.get_argument("confirm", "").strip()

            if not old or not new or not confirm:
                conn.close()
                return self.render("perfil.html",
                    username=username, email=email,
                    bio=row["bio"] or "",
                    photo=current_photo,
                    erro="Preencha todos os campos.", mensagem=None)

            if new != confirm:
                conn.close()
                return self.render("perfil.html",
                    username=username, email=email,
                    bio=row["bio"] or "",
                    photo=current_photo,
                    erro="As senhas não coincidem.", mensagem=None)

            if hash_senha(old) != current_hash:
                conn.close()
                return self.render("perfil.html",
                    username=username, email=email,
                    bio=row["bio"] or "",
                    photo=current_photo,
                    erro="Senha atual incorreta.", mensagem=None)

            if len(new) < 5:
                conn.close()
                return self.render("perfil.html",
                    username=username, email=email,
                    bio=row["bio"] or "",
                    photo=current_photo,
                    erro="Senha deve ter pelo menos 5 caracteres.", mensagem=None)

            new_hash = hash_senha(new)
            c.execute("UPDATE users SET password=? WHERE id=?", (new_hash, user_id))
            conn.commit()
            conn.close()

            return self.render("perfil.html",
                username=username, email=email,
                bio=row["bio"] or "",
                photo=current_photo,
                mensagem="Senha alterada com sucesso.", erro=None)


        # ==================================================
        # ATUALIZAR INFORMAÇÕES
        # ==================================================
        if action == "update_info":

            new_user = self.get_argument("username", username).strip()
            new_email = self.get_argument("email", email).strip()
            new_bio = self.get_argument("bio", "").strip()

            if not new_user or not new_email:
                conn.close()
                return self.render("perfil.html",
                    username=username, email=email,
                    bio=new_bio,
                    photo=current_photo,
                    erro="Usuário e e-mail não podem ficar vazios.", mensagem=None)

            c.execute("SELECT id FROM users WHERE (username=? OR email=?) AND id<>?",
                      (new_user, new_email, user_id))

            if c.fetchone():
                conn.close()
                return self.render("perfil.html",
                    username=username, email=email,
                    bio=new_bio,
                    photo=current_photo,
                    erro="Usuário ou e-mail já em uso.", mensagem=None)

            photo_path = current_photo

            if "photo" in self.request.files:
                photo = self.request.files["photo"][0]
                ext = os.path.splitext(photo["filename"])[1] or ".jpg"

                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                upload_dir = os.path.join(base_dir, "app", "static", "uploads")
                os.makedirs(upload_dir, exist_ok=True)

                fname = f"user_{user_id}{ext}"
                full_path = os.path.join(upload_dir, fname)

                with open(full_path, "wb") as f:
                    f.write(photo["body"])

                photo_path = f"/static/uploads/{fname}"

            c.execute("""
                UPDATE users 
                SET username=?, email=?, bio=?, photo=? 
                WHERE id=?
            """, (new_user, new_email, new_bio, photo_path, user_id))

            conn.commit()
            conn.close()

            return self.render("perfil.html",
                username=new_user, email=new_email,
                bio=new_bio,
                photo=photo_path,
                mensagem="Perfil atualizado com sucesso.",
                erro=None)

        conn.close()
