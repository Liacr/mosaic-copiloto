# Teste isolado: confirma que a chave da API do Gemini funciona.

import sys
from pathlib import Path

caminho_raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(caminho_raiz))

from google import genai
from config.settings import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)
resposta = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Responda só com a palavra: funcionou",
)
print(resposta.text)