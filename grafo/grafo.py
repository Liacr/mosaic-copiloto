# Grafo LangGraph do Mosaic.
# Regra de ouro: decide a rota ANTES de gastar busca vetorial.
# Saudacao nunca toca o banco. Codigo pra auditar sempre vai direto pra auditoria.
# Busca sem relevancia vira recusa com personalidade, sem gastar chamada ao Gemini.
# EXCECAO: se o usuario anexou um PDF, sempre responde (mesmo sem contexto da base).

from langgraph.graph import END, StateGraph

from grafo.estado import EstadoMosaic
from grafo.nos import (
    LIMIAR_DISTANCIA_RELEVANTE,
    no_auditar_e_responder,
    no_decidir_rota,
    no_gerar_resposta,
    no_recuperar_contexto,
    no_responder_fora_de_escopo,
    no_responder_saudacao,
)


def construir_grafo() -> StateGraph:
    grafo = StateGraph(EstadoMosaic)

    grafo.add_node("decidir_rota", no_decidir_rota)
    grafo.add_node("responder_saudacao", no_responder_saudacao)
    grafo.add_node("recuperar_contexto", no_recuperar_contexto)
    grafo.add_node("responder_fora_de_escopo", no_responder_fora_de_escopo)
    grafo.add_node("gerar_resposta", no_gerar_resposta)
    grafo.add_node("auditar_e_responder", no_auditar_e_responder)

    grafo.set_entry_point("decidir_rota")

    def roteamento_inicial(estado: EstadoMosaic) -> str:
        if estado.get("eh_saudacao"):
            return "responder_saudacao"
        return "recuperar_contexto"

    grafo.add_conditional_edges(
        "decidir_rota",
        roteamento_inicial,
        {"responder_saudacao": "responder_saudacao", "recuperar_contexto": "recuperar_contexto"},
    )

    def roteamento_pos_contexto(estado: EstadoMosaic) -> str:
        # Auditoria de CSS tem prioridade absoluta
        if estado.get("codigo_para_auditar"):
            return "auditar_e_responder"

        # Se o usuario anexou um PDF, sempre responde —
        # mesmo que a busca vetorial na base nao ache nada relevante.
        if estado.get("contexto_pdf"):
            return "gerar_resposta"

        contextos = estado.get("contextos", [])
        distancias_vetoriais = [
            c.get("distancia_bruta", c["distancia"])
            for c in contextos if c.get("origem_busca") != "keyword"
        ]
        if not distancias_vetoriais or min(distancias_vetoriais) > LIMIAR_DISTANCIA_RELEVANTE:
            return "responder_fora_de_escopo"

        return "gerar_resposta"

    grafo.add_conditional_edges(
        "recuperar_contexto",
        roteamento_pos_contexto,
        {
            "gerar_resposta": "gerar_resposta",
            "auditar_e_responder": "auditar_e_responder",
            "responder_fora_de_escopo": "responder_fora_de_escopo",
        },
    )

    grafo.add_edge("responder_saudacao", END)
    grafo.add_edge("responder_fora_de_escopo", END)
    grafo.add_edge("gerar_resposta", END)
    grafo.add_edge("auditar_e_responder", END)

    return grafo.compile()


grafo_mosaic = construir_grafo()
