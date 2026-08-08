# Nós do grafo LangGraph.

import re
from typing import Any

from pipeline.geracao import gerar_fora_de_escopo, gerar_resposta, gerar_resposta_com_auditoria, gerar_saudacao
from pipeline.recuperacao import recuperar_contexto

PADRAO_SAUDACAO = re.compile(
    r"^\s*(oi+|ol[áa]|e a[íi]|eae|opa|bom dia|boa tarde|boa noite|hey|hello)[\s!.,?]*$",
    re.IGNORECASE,
)

# distância acima disso = a busca não achou nada realmente relevante.
LIMIAR_DISTANCIA_RELEVANTE = 0.65


def no_decidir_rota(estado: dict[str, Any]) -> dict[str, Any]:
    """Roda ANTES da busca vetorial. Decide se é saudação (não precisa de RAG)."""
    pergunta = estado["pergunta_atual"]
    codigo = estado.get("codigo_para_auditar")

    if not codigo and PADRAO_SAUDACAO.match(pergunta):
        return {"eh_saudacao": True, "oferecer_upload": False}

    pergunta_lower = pergunta.lower()
    # CORREÇÃO: removido "#" que causava falso positivo em qualquer pergunta com número/hashtag
    palavras_token = ["cor", "hex", "espaçamento", "padding", "margin", "tipografia", "fonte", "token", "css"]
    palavras_componente = [
        "componente", "existe", "já tem", "tooltip", "modal", "button", "input", "tag", "preciso de",
        "tabela", "table", "data table", "badge", "status badge", "filtro", "filter bar",
        "vazio", "empty state", "onboarding", "onboarding tooltip",
    ]

    tocou_em_design = any(p in pergunta_lower for p in palavras_token + palavras_componente)
    return {"eh_saudacao": False, "oferecer_upload": tocou_em_design}


def no_responder_saudacao(estado: dict[str, Any]) -> dict[str, Any]:
    """Resposta de apresentação direta - sem busca vetorial, sem chamar o Gemini."""
    return {"resposta_final": gerar_saudacao(), "contextos": []}


def no_recuperar_contexto(estado: dict[str, Any]) -> dict[str, Any]:
    pergunta = estado["pergunta_atual"]
    # CORREÇÃO: aumentado limite de 5 para 7 para dar mais chance de recuperar chunks relevantes
    contextos = recuperar_contexto(pergunta, limite=7)
    return {"contextos": contextos}


def no_responder_fora_de_escopo(estado: dict[str, Any]) -> dict[str, Any]:
    """A busca não achou nada relevante - recusa com personalidade, sem gastar chamada ao Gemini."""
    return {"resposta_final": gerar_fora_de_escopo(), "contextos": []}


def no_gerar_resposta(estado: dict[str, Any]) -> dict[str, Any]:
    pergunta = estado["pergunta_atual"]
    contextos = estado["contextos"]
    incluir_fontes = estado.get("incluir_fontes", True)
    historico = estado.get("historico", "")
    contexto_pdf = estado.get("contexto_pdf")
    contexto_pdf_nome = estado.get("contexto_pdf_nome")

    resultado = gerar_resposta(
        pergunta, contextos,
        incluir_fontes=incluir_fontes,
        historico=historico,
        contexto_pdf=contexto_pdf,
        contexto_pdf_nome=contexto_pdf_nome,
    )
    return {"resposta_final": resultado["texto"]}


def no_auditar_e_responder(estado: dict[str, Any]) -> dict[str, Any]:
    from auditoria.comparador import auditar_codigo

    pergunta = estado["pergunta_atual"]
    contextos = estado["contextos"]
    codigo = estado.get("codigo_para_auditar", "")
    historico = estado.get("historico", "")
    contexto_pdf = estado.get("contexto_pdf")

    if not codigo:
        return {"resposta_final": "Não recebi código para auditar. Pode colar o trecho CSS?"}

    resultado = auditar_codigo(codigo, pergunta_original=pergunta)
    resposta = gerar_resposta_com_auditoria(
        pergunta, contextos, resultado,
        incluir_fontes=False,
        historico=historico,
        contexto_pdf=contexto_pdf,
    )

    return {"resposta_final": resposta["texto"], "resultado_auditoria": resultado}
