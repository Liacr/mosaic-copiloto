# python scripts/testar_extracao.py
# Imprimir no terminal um resumo de cada documento extraído.

import sys
from pathlib import Path

# Adiciona a pasta raiz do projeto ao path do Python, para poder importar os módulos
caminho_raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(caminho_raiz))

from pipeline.extracao import extrair_todos_documentos


def main():
    print("=" * 60)
    print("TESTE DA ETAPA 1: EXTRAÇÃO DE DOCUMENTOS")
    print("=" * 60)

    documentos = extrair_todos_documentos()

    print(f"\nTotal de documentos processados: {len(documentos)}\n")

    for indice, doc in enumerate(documentos, start=1):
        metadados = doc["metadados"]
        print(f"--- Documento {indice} ---")
        print(f"  Arquivo:    {metadados['nome_arquivo']}")
        print(f"  Origem:     {metadados['origem']}")
        print(f"  Categoria:  {metadados['categoria']}")
        print(f"  Componente: {metadados['componente']}")
        print(f"  Formato:    {metadados['formato']}")
        print(f"  Tamanho:    {len(doc['conteudo'])} caracteres")

        amostra = doc["conteudo"][:200].replace("\n", " ")
        print(f"  Amostra:    {amostra}...")
        print()


if __name__ == "__main__":
    main()