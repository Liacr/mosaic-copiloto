# Parser dos tokens oficiais do Carbon.
# A lógica real de parsing e comparação está em comparador.py.
# Este arquivo serve como ponto de extensão para futuras integrações
# com APIs ou arquivos de tokens oficiais do Carbon (ex: DTCG JSON).

from typing import Any


def carregar_tokens_oficiais() -> dict[str, Any]:
    """
    Placeholder: retorna estrutura vazia.
    No futuro, pode carregar de API do Carbon ou arquivo DTCG.
    """
    return {}