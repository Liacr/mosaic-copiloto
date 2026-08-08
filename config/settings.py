import os
import base64
import tempfile
from pathlib import Path

from dotenv import load_dotenv

caminho_raiz = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# 1. Carrega .env local (se existir)
# ---------------------------------------------------------------------------
env_local = caminho_raiz / ".env"
if env_local.exists():
    load_dotenv(env_local)

# ---------------------------------------------------------------------------
# 2. Detecta se está no Streamlit Cloud (st.secrets disponível)
# ---------------------------------------------------------------------------
try:
    import streamlit as st
    _SECRETS = dict(st.secrets) if hasattr(st, "secrets") else {}
except Exception:
    _SECRETS = {}


def _pegar(chave: str, padrao: str = "") -> str:
    """
    Prioridade de leitura:
    1. Streamlit Cloud Secrets (st.secrets)
    2. Variáveis de ambiente (incluindo .env carregado)
    3. Valor padrão
    """
    if chave in _SECRETS:
        return str(_SECRETS[chave])
    return os.getenv(chave, padrao)


# ---------------------------------------------------------------------------
# 3. Configurações do projeto
# ---------------------------------------------------------------------------
NOME_PROJETO = "Mosaic"
NOME_EMPRESA = "Mosaic Labs"

PASTA_DADOS = caminho_raiz / "dados"
PASTA_CARBON = PASTA_DADOS / "carbon"
PASTA_INTERNOS = PASTA_DADOS / "internos"

MODELO_EMBEDDING = _pegar("MODELO_EMBEDDING", "all-MiniLM-L6-v2")
DIMENSAO_VETOR = 384

GEMINI_API_KEY = _pegar("GEMINI_API_KEY")

# ---------------------------------------------------------------------------
# 4. Oracle — credenciais
# ---------------------------------------------------------------------------
ORACLE_USER = _pegar("ORACLE_USER", "ADMIN")
ORACLE_PASSWORD = _pegar("ORACLE_PASSWORD")
ORACLE_DSN = _pegar("ORACLE_DSN")
ORACLE_WALLET_PASSWORD = _pegar("ORACLE_WALLET_PASSWORD")

# ---------------------------------------------------------------------------
# 5. Wallet — local (pasta física) ou remoto (reconstruído dos secrets)
# ---------------------------------------------------------------------------
PASTA_WALLET_LOCAL = caminho_raiz / "config" / "wallet"


def _reconstruir_wallet() -> Path:
    """Reconstrói a pasta wallet em disco a partir dos secrets base64.
    Usado no Streamlit Cloud, onde não podemos subir arquivos binários."""
    pasta_temp = Path(tempfile.gettempdir()) / "wallet_mosaic"

    # Se já existe e tem arquivos, reusa
    if pasta_temp.exists() and any(pasta_temp.iterdir()):
        return pasta_temp

    pasta_temp.mkdir(parents=True, exist_ok=True)

    # Lista de arquivos típicos do wallet Oracle
    nomes_wallet = [
        "tnsnames.ora", "sqlnet.ora", "cwallet.sso", "ewallet.pem",
        "ojdbc.properties", "keystore.jks", "truststore.jks"
    ]

    reconstruidos = 0
    for nome in nomes_wallet:
        chave_secret = f"WALLET_{nome.replace('.', '_').upper()}"
        conteudo_b64 = _pegar(chave_secret, "")

        if conteudo_b64:
            try:
                (pasta_temp / nome).write_bytes(base64.b64decode(conteudo_b64))
                reconstruidos += 1
            except Exception as e:
                print(f"[Settings] Aviso: não consegui reconstruir {nome}: {e}")

    if reconstruidos == 0:
        print("[Settings] Aviso: nenhum arquivo de wallet reconstruído dos secrets.")
    else:
        print(f"[Settings] Wallet reconstruída em {pasta_temp} ({reconstruidos} arquivos)")

    return pasta_temp


# Decide qual pasta usar: local (se existe) ou reconstruída dos secrets
PASTA_WALLET = PASTA_WALLET_LOCAL if PASTA_WALLET_LOCAL.exists() else _reconstruir_wallet()
