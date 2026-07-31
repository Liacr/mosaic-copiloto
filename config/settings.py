import os
from pathlib import Path

from dotenv import load_dotenv # Pra ler o arquivo .env

caminho_raiz = Path(__file__).resolve().parent.parent
load_dotenv(caminho_raiz / ".env")


def pegar_variavel(nome: str, padrao: str = "") -> str:
    """
    Lê uma variável de ambiente.
    Se não existir, retorna o valor padrão (ou string vazia).
    """
    return os.getenv(nome, padrao)


#Config projeto
NOME_PROJETO = "Mosaic"
NOME_EMPRESA = "Mosaic Labs"

#Caminhos de pastas
PASTA_DADOS = caminho_raiz / "dados"
PASTA_CARBON = PASTA_DADOS / "carbon"
PASTA_INTERNOS = PASTA_DADOS / "internos"

#Modelo de embedding
MODELO_EMBEDDING = pegar_variavel("MODELO_EMBEDDING", "all-MiniLM-L6-v2")

#API
GEMINI_API_KEY = pegar_variavel("GEMINI_API_KEY")

#Banco Oracle
ORACLE_USER = pegar_variavel("ORACLE_USER", "ADMIN")
ORACLE_PASSWORD = pegar_variavel("ORACLE_PASSWORD")
ORACLE_DSN = pegar_variavel("ORACLE_DSN")