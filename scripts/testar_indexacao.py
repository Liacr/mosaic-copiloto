# Teste da Etapa 3: indexa tudo no Oracle e faz uma busca de teste.

import sys
from pathlib import Path

caminho_raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(caminho_raiz))

from pipeline.indexacao import (
    buscar_similar,
    carregar_modelo_embedding,
    conectar_oracle,
    criar_tabela_chunks,
    executar_indexacao_completa,
    limpar_tabela_chunks,
)


def testar_busca():
    """Indexa tudo e testa buscas com e sem filtro de categoria."""
    print("=" * 60)
    print("ETAPA 3: INDEXAÇÃO + BUSCA VETORIAL")
    print("=" * 60)

    # 1. Indexa todos os chunks
    executar_indexacao_completa()

    # 2. Testa buscas
    print("\n" + "=" * 60)
    print("TESTE DE BUSCA")
    print("=" * 60)

    conexao = conectar_oracle()
    modelo = carregar_modelo_embedding()

    perguntas = [
        ("Qual token de cor eu uso pro botão primário?", "tokens"),
        ("Meu CSS usa #2979FF pro botão, isso bate com o padrão?", None),
        ("Já existe um componente de Tooltip?", "componentes"),
        ("Como deve ser o alinhamento de botões em um modal?", "componentes"),
    ]

    for pergunta, categoria in perguntas:
        print(f"\n❓ Pergunta: {pergunta}")
        if categoria:
            print(f"   Filtro: categoria = {categoria}")

        resultados = buscar_similar(conexao, modelo, pergunta, categoria=categoria, limite=3)

        for i, res in enumerate(resultados, 1):
            print(f"   {i}. [{res['categoria']}] {res['nome_arquivo']} (distância: {res['distancia']:.4f})")
            amostra = res['conteudo'][:120].replace('\n', ' ')
            print(f"      → {amostra}...")

    conexao.close()


if __name__ == "__main__":
    testar_busca()