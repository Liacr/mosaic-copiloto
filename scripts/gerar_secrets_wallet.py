"""
Script para codificar a pasta wallet/ do Oracle em base64.
Rode uma vez no seu PC local, copie a saída e cole no Secrets do Streamlit Cloud.

Como usar:
    python scripts/gerar_secrets_wallet.py
"""

import base64
from pathlib import Path

caminho_raiz = Path(__file__).resolve().parent.parent
pasta_wallet = caminho_raiz / "config" / "wallet"

if not pasta_wallet.exists():
    print(f"❌ Pasta wallet não encontrada: {pasta_wallet}")
    print("   Certifique-se de que a pasta config/wallet/ existe com os arquivos do Oracle.")
    exit(1)

print("=" * 70)
print("SECRETS DO WALLET ORACLE — COPIE TUDO ABAIXO")
print("=" * 70)
print()

arquivos = sorted(pasta_wallet.iterdir())
if not arquivos:
    print("❌ Pasta wallet está vazia!")
    exit(1)

for arquivo in arquivos:
    if arquivo.is_file():
        b64 = base64.b64encode(arquivo.read_bytes()).decode()
        chave = f"WALLET_{arquivo.name.replace('.', '_').upper()}"
        print(f'{chave} = "{b64}"')

print()
print("=" * 70)
print("✅ Copie todo o bloco acima e cole em:")
print("   share.streamlit.io → Seu app → ⋮ → Settings → Secrets")
print("=" * 70)
