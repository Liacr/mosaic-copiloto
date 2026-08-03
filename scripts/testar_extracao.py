# Teste das Etapas 1 e 2 — mostra um resumo por arquivo para confirmar que tudo foi processado.

import sys
from pathlib import Path

caminho_raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(caminho_raiz))

from pipeline.chunking import gerar_todos_chunks


def main():
    print("=" * 60)
    print("TESTE: EXTRAÇÃO + CHUNKING")
    print("=" * 60)

    chunks = gerar_todos_chunks()

    # Agrupa chunks por arquivo de origem
    por_arquivo = {}
    por_categoria = {}

    for chunk in chunks:
        nome_arquivo = chunk["metadados"]["nome_arquivo"]
        categoria = chunk["metadados"]["categoria"]

        if nome_arquivo not in por_arquivo:
            por_arquivo[nome_arquivo] = {
                "categoria": categoria,
                "componente": chunk["metadados"].get("componente"),
                "origem": chunk["metadados"]["origem"],
                "formato": chunk["metadados"]["formato"],
                "total_chunks": 0,
                "primeiro_chunk": chunk["conteudo"][:250].replace("\n", " "),
            }
        por_arquivo[nome_arquivo]["total_chunks"] += 1
        por_categoria[categoria] = por_categoria.get(categoria, 0) + 1

    print(f"\nTotal de documentos: {len(por_arquivo)}")
    print(f"Total de chunks: {len(chunks)}\n")

    print("-" * 60)
    print("RESUMO POR ARQUIVO")
    print("-" * 60)
    for nome, info in sorted(por_arquivo.items()):
        print(f"\n📄 {nome}")
        print(f"   Origem: {info['origem']} | Categoria: {info['categoria']} | Componente: {info['componente']}")
        print(f"   Formato: {info['formato']} | Chunks: {info['total_chunks']}")
        print(f"   Amostra: {info['primeiro_chunk']}...")

    print("\n" + "-" * 60)
    print("DISTRIBUIÇÃO POR CATEGORIA")
    print("-" * 60)
    for cat, qtd in sorted(por_categoria.items()):
        print(f"  {cat}: {qtd} chunks")


if __name__ == "__main__":
    main()