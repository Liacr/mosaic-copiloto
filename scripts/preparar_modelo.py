# Baixa o modelo de embedding UMA VEZ e deixa em cache local.
# Rode ANTES do deploy: python scripts/preparar_modelo.py

from sentence_transformers import SentenceTransformer
from config.settings import MODELO_EMBEDDING

print(f"Baixando modelo {MODELO_EMBEDDING}...")
modelo = SentenceTransformer(MODELO_EMBEDDING)
print("Modelo baixado e cacheado com sucesso.")
print(f"Cache local: ~/.cache/torch/sentence_transformers/")