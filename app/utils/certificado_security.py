"""
Módulo de Segurança para Certificados
Implementa validação, auditoria e verificação de integridade de certificados.
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")


def conectar():
    """Cria conexão com banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def gerar_token_certificado():
    """
    Gera um token único seguro para certificado.
    Formato: 32 caracteres hexadecimais
    """
    return secrets.token_hex(16)


def gerar_hash_certificado(user_id, modulo, nota, data):
    """
    Gera um hash verificável do certificado.
    Usado para detectar alterações não autorizadas.
    """
    dados = f"{user_id}|{modulo}|{nota}|{data}"
    return hashlib.sha256(dados.encode()).hexdigest()


def registrar_certificado(user_id, modulo, nota, data_conclusao):
    """
    Registra um novo certificado no banco de dados com token e hash.
    Retorna o token único do certificado.
    """
    token = gerar_token_certificado()
    hash_cert = gerar_hash_certificado(user_id, modulo, nota, data_conclusao)
    data_geracao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO certificados 
            (user_id, modulo, nota, data_conclusao, token, hash, data_geracao, ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (user_id, modulo, nota, data_conclusao, token, hash_cert, data_geracao))
        
        conn.commit()
        cert_id = cursor.lastrowid
        conn.close()
        
        return {
            "id": cert_id,
            "token": token,
            "hash": hash_cert
        }
    except Exception as e:
        conn.close()
        raise Exception(f"Erro ao registrar certificado: {str(e)}")


def validar_token_certificado(token):
    """
    Valida se um token de certificado é válido e retorna os dados.
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, modulo, nota, data_conclusao, hash, ativo
        FROM certificados
        WHERE token = ? AND ativo = 1
        LIMIT 1
    """, (token,))

    resultado = cursor.fetchone()
    conn.close()

    if not resultado:
        return None

    return dict(resultado)


def verificar_integridade_certificado(token, user_id=None):
    """
    Verifica se o certificado não foi alterado.
    Retorna True se válido, False caso contrário.
    """
    cert = validar_token_certificado(token)

    if not cert:
        return False

    # Se user_id foi fornecido, valida que pertence ao usuário
    if user_id and cert["user_id"] != user_id:
        return False

    # Recalcula o hash e compara
    hash_esperado = gerar_hash_certificado(
        cert["user_id"],
        cert["modulo"],
        cert["nota"],
        cert["data_conclusao"]
    )

    return cert["hash"] == hash_esperado


def registrar_acesso_certificado(user_id, token, ip_address, tipo_acesso="view"):
    """
    Registra tentativa de acesso ao certificado para auditoria.
    tipo_acesso: 'view', 'download', 'verify', 'denied'
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO auditoria_certificados
            (user_id, token_certificado, ip_address, tipo_acesso, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, token, ip_address, tipo_acesso, timestamp))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Erro ao registrar acesso: {str(e)}")
        return False


def detectar_acesso_suspeito(ip_address, janela_minutos=5, limite_tentativas=10):
    """
    Detecta se há múltiplas tentativas de acesso negado do mesmo IP.
    Retorna True se suspeita de ataque.
    """
    tempo_limite = (
        datetime.now() - timedelta(minutes=janela_minutos)
    ).strftime("%Y-%m-%d %H:%M:%S")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as tentativas
        FROM auditoria_certificados
        WHERE ip_address = ? AND tipo_acesso = 'denied' AND timestamp > ?
    """, (ip_address, tempo_limite))

    resultado = cursor.fetchone()
    conn.close()

    tentativas = resultado["tentativas"] if resultado else 0
    return tentativas >= limite_tentativas


def bloquear_ip(ip_address, motivo="Múltiplas tentativas de acesso negado"):
    """
    Bloqueia um IP suspeito.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT OR REPLACE INTO ips_bloqueados
            (ip_address, motivo, data_bloqueio, ativo)
            VALUES (?, ?, ?, 1)
        """, (ip_address, motivo, timestamp))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Erro ao bloquear IP: {str(e)}")
        return False


def ip_esta_bloqueado(ip_address):
    """
    Verifica se um IP está bloqueado.
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ativo FROM ips_bloqueados
        WHERE ip_address = ? AND ativo = 1
        LIMIT 1
    """, (ip_address,))

    resultado = cursor.fetchone()
    conn.close()

    return resultado is not None


def obter_historico_certificado(token, limite=50):
    """
    Retorna histórico de acessos a um certificado.
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, ip_address, tipo_acesso, timestamp
        FROM auditoria_certificados
        WHERE token_certificado = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (token, limite))

    resultados = cursor.fetchall()
    conn.close()

    return [dict(row) for row in resultados]


def invalidar_certificado(token, motivo="Certificado revogado"):
    """
    Invalida um certificado (marca como não ativo).
    Usado para revogar certificados em caso de fraude.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE certificados
            SET ativo = 0
            WHERE token = ?
        """, (token,))

        # Registra a revogação
        cursor.execute("""
            INSERT INTO auditoria_certificados
            (token_certificado, tipo_acesso, timestamp)
            VALUES (?, 'revoked', ?)
        """, (token, timestamp))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Erro ao invalidar certificado: {str(e)}")
        return False


def criar_tabelas_seguranca():
    """
    Cria as tabelas necessárias para o sistema de segurança.
    Execute uma única vez no início.
    """
    conn = conectar()
    cursor = conn.cursor()

    try:
        # Tabela de certificados com tokens
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                modulo INTEGER NOT NULL,
                nota INTEGER NOT NULL,
                data_conclusao TEXT,
                token TEXT UNIQUE NOT NULL,
                hash TEXT NOT NULL,
                data_geracao TEXT NOT NULL,
                ativo INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Tabela de auditoria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auditoria_certificados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token_certificado TEXT,
                ip_address TEXT,
                tipo_acesso TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Tabela de IPs bloqueados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ips_bloqueados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                motivo TEXT,
                data_bloqueio TEXT NOT NULL,
                ativo INTEGER DEFAULT 1
            )
        """)

        conn.commit()
        conn.close()
        print("✅ Tabelas de segurança criadas com sucesso!")
        return True

    except Exception as e:
        conn.close()
        print(f"❌ Erro ao criar tabelas: {str(e)}")
        return False
