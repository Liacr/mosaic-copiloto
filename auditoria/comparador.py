# Auditoria deterministica com sugestao contextual refinada.
# Cores: query especifica por tipo de elemento. Espacamento: match exato + validacao contra escala oficial.

import re
from typing import Any

from pipeline.indexacao import buscar_similar, carregar_modelo_embedding, conectar_oracle

# Escala oficial de espacamento do Carbon Design System (em px)
ESCALA_ESPACAMENTO_CARBON = [2, 4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96, 160]


def extrair_valores_css(codigo: str) -> list[dict[str, Any]]:
    valores = []

    padrao_hex = r'#[0-9A-Fa-f]{3,8}\b'
    for match in re.finditer(padrao_hex, codigo):
        valores.append({
            "propriedade": "color",
            "valor": match.group().lower(),
            "tipo": "cor",
            "posicao": match.start(),
        })

    padrao_spacing = r'(padding|margin|gap|top|right|bottom|left)\s*:\s*(\d+(?:\.\d+)?)(px|rem)\b'
    for match in re.finditer(padrao_spacing, codigo, re.IGNORECASE):
        valores.append({
            "propriedade": match.group(1).lower(),
            "valor": match.group(2) + match.group(3),
            "tipo": "espacamento",
            "posicao": match.start(),
        })

    padrao_px_rem = r'(\d+(?:\.\d+)?)(px|rem)\b'
    for match in re.finditer(padrao_px_rem, codigo):
        val = match.group(1) + match.group(2)
        if not any(v["valor"] == val and v["tipo"] == "espacamento" for v in valores):
            valores.append({
                "propriedade": "spacing",
                "valor": val,
                "tipo": "espacamento",
                "posicao": match.start(),
            })

    return valores


def _validar_espacamento_contra_escala(valor_str: str) -> dict[str, Any] | None:
    """Valida um valor de espacamento contra a escala oficial do Carbon.
    Retorna dict com status e sugestao, ou None se nao for espacamento reconhecivel."""
    match = re.match(r"(\d+(?:\.\d+)?)(px|rem)", valor_str.lower())
    if not match:
        return None

    numero = float(match.group(1))
    unidade = match.group(2)

    # Converte rem para px (assumindo base 16px) para comparar com a escala
    if unidade == "rem":
        numero_px = numero * 16
    else:
        numero_px = numero

    # Arredonda para inteiro (a escala do Carbon e toda em inteiros)
    numero_px_int = round(numero_px)

    if numero_px_int in ESCALA_ESPACAMENTO_CARBON:
        return {
            "status": "CONFORME",
            "valor_oficial": f"{numero_px_int}px",
            "sugestao": None,
            "fonte": "escala-oficial-carbon",
        }

    # Nao esta na escala: sugere o valor mais proximo
    mais_proximo = min(ESCALA_ESPACAMENTO_CARBON, key=lambda x: abs(x - numero_px_int))
    return {
        "status": "NAO CONFORME",
        "valor_oficial": "fora da escala",
        "sugestao": f"{mais_proximo}px",
        "fonte": "escala-oficial-carbon",
    }


def buscar_token_oficial(
    valor_procurado: str,
    contexto_semantico: str | None = None,
    tipo_item: str = "cor",
    propriedade_css: str = "color",
) -> dict[str, Any] | None:
    """
    1. Busca exata: o valor procurado aparece literalmente no chunk.
    2. Se nao achar e for COR: busca por contexto tipificado com query sintetica.
    3. Se nao achar e for ESPACAMENTO: retorna None (a validacao da escala e feita em auditar_codigo).
    """
    conexao = conectar_oracle()
    try:
        modelo = carregar_modelo_embedding()

        # TENTATIVA 1: busca exata pelo valor
        resultados = buscar_similar(
            conexao=conexao, modelo=modelo, pergunta=valor_procurado, categoria="tokens", limite=5
        )

        valor_lower = valor_procurado.lower()
        for res in resultados:
            if valor_lower in res["conteudo"].lower():
                return {"tipo_match": "exato", "token": res}

        # TENTATIVA 2: busca por contexto (SO PARA CORES)
        if contexto_semantico and tipo_item == "cor":
            if "background" in propriedade_css:
                query_sintetica = "token cor background fundo"
            elif "border" in propriedade_css:
                query_sintetica = "token cor borda border"
            else:
                query_sintetica = "token cor botao primario acao interativa"

            resultados_contexto = buscar_similar(
                conexao=conexao, modelo=modelo, pergunta=query_sintetica, categoria="tokens", limite=1
            )
            if resultados_contexto:
                return {"tipo_match": "sugestao_por_contexto", "token": resultados_contexto[0]}

    finally:
        conexao.close()

    return None


def auditar_codigo(codigo: str, pergunta_original: str | None = None) -> dict[str, Any]:
    valores_extraidos = extrair_valores_css(codigo)
    itens_auditoria = []

    for item in valores_extraidos:
        # CORRECAO: para espacamento, valida primeiro contra a escala oficial do Carbon
        # (deterministico, nao depende de embedding que nao entende numeros)
        if item["tipo"] == "espacamento":
            validacao_escala = _validar_espacamento_contra_escala(item["valor"])
            if validacao_escala:
                itens_auditoria.append({
                    "elemento": item["propriedade"],
                    "valor_encontrado": item["valor"],
                    "valor_oficial": validacao_escala["valor_oficial"],
                    "sugestao_contextual": None,
                    "status": validacao_escala["status"],
                    "tipo": item["tipo"],
                    "fonte": validacao_escala["fonte"],
                    "sugestao_escala": validacao_escala.get("sugestao"),
                })
                continue

        # Para cores (e espacamento que nao bateu na escala): busca na base vetorial
        resultado_busca = buscar_token_oficial(
            item["valor"],
            contexto_semantico=pergunta_original,
            tipo_item=item["tipo"],
            propriedade_css=item["propriedade"],
        )

        valor_oficial = "token nao encontrado"
        sugestao_contextual = None
        status = "NAO CONFORME"
        fonte = None

        if resultado_busca:
            conteudo = resultado_busca["token"]["conteudo"]
            match = re.search(r'valor\s+([^\s,]+)', conteudo)
            valor_no_chunk = match.group(1) if match else None

            if resultado_busca["tipo_match"] == "exato":
                valor_oficial = valor_no_chunk or "nao identificado"
                status = "CONFORME" if item["valor"].lower() == valor_oficial.lower() else "NAO CONFORME"
                fonte = resultado_busca["token"]["nome_arquivo"]
            else:
                sugestao_contextual = {
                    "valor": valor_no_chunk or "nao identificado",
                    "fonte": resultado_busca["token"]["nome_arquivo"],
                }

        itens_auditoria.append({
            "elemento": item["propriedade"],
            "valor_encontrado": item["valor"],
            "valor_oficial": valor_oficial,
            "sugestao_contextual": sugestao_contextual,
            "status": status,
            "tipo": item["tipo"],
            "fonte": fonte,
            "sugestao_escala": None,
        })

    return {
        "itens": itens_auditoria,
        "conforme_geral": all(i["status"] == "CONFORME" for i in itens_auditoria) if itens_auditoria else None,
    }


def montar_veredito_deterministico(item: dict) -> str:
    elemento = item["elemento"]
    encontrado = item["valor_encontrado"]
    status = item["status"]
    oficial = item["valor_oficial"]
    sugestao = item.get("sugestao_contextual")
    tipo = item.get("tipo", "cor")
    sugestao_escala = item.get("sugestao_escala")
    fonte = item.get("fonte")

    if status == "CONFORME":
        if tipo == "espacamento" and fonte == "escala-oficial-carbon":
            return f"✅ **{elemento}** (`{encontrado}`): conforme — valor valido na escala oficial de espacamento do Carbon."
        return f"✅ **{elemento}** (`{encontrado}`): conforme — bate com o token oficial `{oficial}`."

    if tipo == "espacamento" and sugestao_escala:
        return (
            f"❌ **{elemento}** (`{encontrado}`): nao conforme. "
            f"Nao esta na escala oficial de espacamento do Carbon. "
            f"O valor mais proximo e `{sugestao_escala}`."
        )

    if oficial != "token nao encontrado" and oficial != "fora da escala":
        return f"❌ **{elemento}** (`{encontrado}`): nao conforme. O token oficial e `{oficial}`."

    if sugestao:
        return (
            f"⚠️ **{elemento}** (`{encontrado}`): nao e um token oficial. Nao achei correspondencia exata, "
            f"mas o mais proximo no contexto e `{sugestao['valor']}` (fonte: {sugestao['fonte']}) — vale confirmar antes de usar."
        )

    # Sem sugestao: diferencia mensagem entre cor e espacamento
    if tipo == "espacamento":
        return (
            f"❓ **{elemento}** (`{encontrado}`): nao e um token oficial de espacamento do Carbon. "
            f"Os valores validos sao: {', '.join(f'{v}px' for v in ESCALA_ESPACAMENTO_CARBON)}. "
            f"Recomendo usar o mais proximo ou falar com o Design Ops."
        )

    return (
        f"❓ **{elemento}** (`{encontrado}`): nao e token oficial e nao achei nada parecido na base. "
        f"Recomendo falar com o Design Ops."
    )
