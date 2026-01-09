import sys
import sqlite3
import hashlib
DB = "usuarios.db"

def conectar():
    return sqlite3.connect(DB)


def listar_usuarios():
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT id, username, email FROM users ORDER BY id")
    usuarios = c.fetchall()

    conn.close()

    print("\n" + "="*50)
    print("===  RELATÓRIO DE USUÁRIOS (Login & Email) ===")
    
    print("="*50)
    
    if not usuarios:
        print("Nenhum usuário cadastrado.")
        print("="*50)
        return
        
    print(f"{'ID':<4} | {'USUÁRIO':<20} | {'EMAIL':<25}")
    print("-" * 50)

    for u in usuarios:
        print(f"{u[0]:<4} | {u[1]:<20} | {u[2]:<25}")
    
    print("=" * 50)



def listar_senhas_de_usuarios():
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT id, username, password, email FROM users ORDER BY id")
    usuarios = c.fetchall()

    conn.close()

    print("\n" + "="*80)
    print("===  RELATÓRIO DE SENHAS (HASH ATUAL) ===")
    print("="*80)
    if not usuarios:
        print("Nenhum usuário cadastrado.")
        print("="*80)
        return

    print(f"{'ID':<4} | {'USUÁRIO':<20} | {'EMAIL':<25} | {'HASH DA SENHA (SHA256)':<64}")
    print("-" * 120) 

    for u in usuarios:

        print(f"{u[0]:<4} | {u[1]:<20} | {u[3]:<25} | {u[2]}")
        
    print("=" * 120)

def listar_detalhes_de_senha():
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT id, username, password FROM users ORDER BY id")
    usuarios = c.fetchall()

    conn.close()

    print("\n" + "="*80)
    print("===  DETALHES DE SENHA E RECUPERAÇÃO ===")
    print("="*80)
    if not usuarios:
        print("Nenhum usuário cadastrado.")
        print("="*80)
        return

    print("\nAVISO IMPORTANTE:")
    print("> Os campos 'Token' e 'Redefinição' são SIMULADOS, pois requerem colunas adicionais no DB.")
    print("> 'Senha de Cadastro (Hash Atual)' mostra o HASH da senha que está no DB neste momento.")
    print("-" * 80)
    
    for u in usuarios:
        user_id, username, password_hash = u[0], u[1], u[2]
        
        token_simulado = "Token Ativo: 1a2b3c4d5e" 
        redefinicao_simulada = "Redefinida em: 2025-12-25"

        print(f"\n|--------------------- USUÁRIO ID: {user_id} ({username}) --------------------|")
        
        print(f"| Login: {username:<20} |")
        print(f"| Senha de Cadastro (Hash Atual): {password_hash} |")

        print(f"| {'Token de Recuperação (Simulado)':<30} | {token_simulado:<40} |")
        print(f"| {'Houve Redefinição (Simulado)':<30} | {redefinicao_simulada:<40} |")
        print("|" + "-"*78 + "|")
        
    print("\n" + "=" * 80)
    

def cadastrar_usuario():
    nome = input("Nome do usuário: ").strip()
    email = input("Email do usuário: ").strip()
    senha = input("Senha do usuário: ").strip()

    if not nome or not email or not senha:
        print("  Todos os campos são obrigatórios.")
        return

    senha_hash = hashlib.sha256(senha.encode()).hexdigest()

    try:
        conn = conectar()
        c = conn.cursor()

        c.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (nome, senha_hash, email)
        )

        conn.commit()
        conn.close()

        print("  Usuário cadastrado com sucesso!")

    except sqlite3.IntegrityError:
        print("  Usuário ou email já existe.")
    except Exception as e:
        print(f" Erro: {e}")


def deletar_usuario(user_id):
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not c.fetchone():
        conn.close()
        return False, "Usuário não encontrado"

    try:
        c.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        return True, "Usuário deletado com sucesso"
    except Exception as e:
        conn.close()
        return False, f"Erro ao deletar usuário: {str(e)}"


def menu():
    opcoes = {
        "1": ("Listar usuários (Login/Email)", listar_usuarios),
        "2": ("Listar usuários (Hash da Senha ATUAL)", listar_senhas_de_usuarios),
        "3": ("Cadastrar usuário", cadastrar_usuario),
        "4": ("Deletar usuário", deletar_usuario),
        "5": ("Detalhes de Senha e Recuperação", listar_detalhes_de_senha), 
        "0": ("Sair", None)
    }

    while True:
        print("\n" + "="*30)
        print("=== MENU ADMIN ===")
        print("="*30)
        for k, v in opcoes.items():
            print(f"{k}. {v[0]}")
        print("="*30)

        escolha = input("Escolha a opção: ").strip()

        if escolha == "0":
            print("\n Saindo...")
            sys.exit(0)
        elif escolha in opcoes:
            opcoes[escolha][1]()
        else:
            print("  Opção inválida. Tente novamente.")


if __name__ == "__main__":
    menu()