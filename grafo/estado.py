# Estado que circula entre os nós do grafo LangGraph.

from typing import Annotated, Any

from typing_extensions import TypedDict


def adicionar_mensagens(esquerda: list, direita: list) -> list:
    return esquerda + direita


class EstadoMosaic(TypedDict):
    mensagens: Annotated[list[dict[str, str]], adicionar_mensagens]
    pergunta_atual: str
    contextos: list[dict[str, Any]]
    resultado_auditoria: dict[str, Any] | None
    oferecer_upload: bool      # decidido pelo nó de rota, nunca parseando texto
    eh_saudacao: bool          # decidido pelo nó de geração, nunca parseando texto
    codigo_para_auditar: str | None
    resposta_final: str
    contexto_pdf: str | None   # texto extraído de PDF anexado pelo usuário na sidebar
