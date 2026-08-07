# ETAPA 4: Recuperação (RAG)
# Usa singleton do modelo para não recarregar a cada pergunta.
# Query expansion + busca híbrida (vetorial + keyword) com fallback
# disparado por qualidade do resultado, não por quantidade.

from typing import Any

from pipeline.indexacao import buscar_similar, carregar_modelo_embedding, conectar_oracle

PALAVRAS_TOKENS = [
    "cor", "hex", "hexadecimal", "#", "espaçamento", "spacing", "padding",
    "margin", "tipografia", "fonte", "tamanho", "px", "rem", "token", "css",
]

PALAVRAS_COMPONENTES = [
    "componente", "existe", "já tem", "tem um", "preciso de", "quero um",
    "tooltip", "modal", "button", "input", "tag",
    "tabela", "table", "data table", "badge", "status badge", "filtro", "filter bar",
    "vazio", "empty state", "onboarding", "onboarding tooltip",
]

EXPANSAO_COMPONENTES = {
    "tabela": "data table grid listagem tabela",
    "table": "data table grid listagem tabela",
    "data table": "data table grid listagem tabela",
    "badge": "status badge indicador estado",
    "status badge": "status badge indicador estado",
    "filtro": "filter bar busca filtro",
    "filter bar": "filter bar busca filtro",
    "vazio": "empty state vazio sem resultado",
    "empty state": "empty state vazio sem resultado",
    "onboarding": "onboarding tooltip introdução novidade",
    "onboarding tooltip": "onboarding tooltip introdução novidade",
}

# Distância de cosseno acima da qual o resultado é considerado fraco
# demais pra confiar só na busca vetorial. Ajustar depois de observar
# mais buscas reais — 0.55 é ponto de partida razoável.
DISTANCIA_MAXIMA_ACEITAVEL = 0.6


def decidir_filtro(pergunta: str) -> str | None:
    pergunta_lower = pergunta.lower()
    if any(p in pergunta_lower for p in PALAVRAS_TOKENS):
        return "tokens"
    if any(p in pergunta_lower for p in PALAVRAS_COMPONENTES):
        return "componentes"
    return None


def _expandir_query(pergunta: str) -> str:
    pergunta_lower = pergunta.lower()
    termos_extra = []
    for chave, expansao in EXPANSAO_COMPONENTES.items():
        if chave in pergunta_lower:
            termos_extra.append(expansao)
    if termos_extra:
        return f"{pergunta} {' '.join(termos_extra)}"
    return pergunta


def _buscar_por_keyword(
    conexao,
    pergunta: str,
    categoria: str | None,
    limite: int,
) -> list[dict[str, Any]]:
    """Fallback por keyword — usa bind variables, nunca concatena texto do
    usuário direto na string SQL (isso seria uma brecha de SQL injection)."""
    cursor = conexao.cursor()
    palavras = [p for p in pergunta.lower().split() if len(p) > 3][:4]
    if not palavras:
        return []

    condicoes = []
    binds: dict[str, Any] = {}
    for i, p in enumerate(palavras):
        chave = f"palavra{i}"
        condicoes.append(f"LOWER(conteudo) LIKE :{chave}")
        binds[chave] = f"%{p}%"

    likes = " OR ".join(condicoes)
    binds["limite"] = limite

    if categoria:
        binds["categoria"] = categoria
        sql = f"""
            SELECT id, conteudo, categoria, origem, componente, nome_arquivo, 0.0 as distancia
            FROM chunks_mosaic
            WHERE categoria = :categoria AND ({likes})
            FETCH FIRST :limite ROWS ONLY
        """
    else:
        sql = f"""
            SELECT id, conteudo, categoria, origem, componente, nome_arquivo, 0.0 as distancia
            FROM chunks_mosaic
            WHERE {likes}
            FETCH FIRST :limite ROWS ONLY
        """

    cursor.execute(sql, binds)

    resultados = []
    for row in cursor:
        conteudo = row[1]
        if hasattr(conteudo, "read"):
            conteudo = conteudo.read()
        resultados.append({
            "id": row[0],
            "conteudo": conteudo,
            "categoria": row[2],
            "origem": row[3],
            "componente": row[4],
            "nome_arquivo": row[5],
            "distancia": row[6],
        })
    cursor.close()
    return resultados


def recuperar_contexto(pergunta: str, limite: int = 7) -> list[dict[str, Any]]:
    categoria = decidir_filtro(pergunta)
    conexao = conectar_oracle()
    query_expandida = _expandir_query(pergunta)

    try:
        modelo = carregar_modelo_embedding()

        resultados_vetorial = buscar_similar(
            conexao=conexao,
            modelo=modelo,
            pergunta=query_expandida,
            categoria=categoria,
            limite=limite,
        )

        # Fallback por keyword: dispara pela QUALIDADE do melhor resultado,
        # não pela quantidade — FETCH FIRST sempre retorna N linhas se
        # existirem, então "poucos resultados" quase nunca acontece de
        # verdade, mesmo quando a busca é ruim.
        melhor_distancia = resultados_vetorial[0]["distancia"] if resultados_vetorial else 999
        resultados_keyword = []
        if not resultados_vetorial or melhor_distancia > DISTANCIA_MAXIMA_ACEITAVEL:
            resultados_keyword = _buscar_por_keyword(conexao, pergunta, categoria, limite=5)

        vistos = set()
        resultados = []
        for r in resultados_vetorial + resultados_keyword:
            if r["id"] not in vistos:
                vistos.add(r["id"])
                resultados.append(r)
            if len(resultados) >= limite:
                break

    finally:
        conexao.close()

    print(f"\n[DEBUG RAG] Pergunta: '{pergunta}' | Query expandida: '{query_expandida}' | Filtro: {categoria} | Chunks: {len(resultados)}")
    for i, r in enumerate(resultados[:5], 1):
        amostra = r['conteudo'][:100].replace('\n', ' ')
        print(f"  [{i}] {r['nome_arquivo']} [{r['categoria']}] (dist: {r['distancia']:.4f}): {amostra}...")

    return resultados