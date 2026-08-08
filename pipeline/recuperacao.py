# ETAPA 4: Recuperacao (RAG)
# Usa singleton do modelo para nao recarregar a cada pergunta.
# Busca hibrida (vetorial + keyword) com reranker simples.
# REGRA: manter as listas de palavras-chave MINIMAS e genericas.
# Nao liste componente por componente — o embedding entende sinonimos sozinho.

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Any

from pipeline.indexacao import buscar_similar, carregar_modelo_embedding, conectar_oracle

# Palavras-chave MINIMAS para detectar se a pergunta e sobre tokens/cores.
PALAVRAS_TOKENS = [
    "cor", "hex", "hexadecimal", "#", "espacamento", "spacing", "padding",
    "margin", "tipografia", "fonte", "tamanho", "px", "rem", "token", "css",
    "modo escuro", "dark mode", "tema escuro",
]

# Palavras-chave MINIMAS para detectar se a pergunta e sobre componentes.
PALAVRAS_COMPONENTES = [
    "componente", "existe", "ja tem", "tem um", "preciso de", "quero um",
    "existe um", "ja existe", "tem algum",
]

# Distancia de cosseno acima da qual o resultado e considerado fraco
# demais pra confiar so na busca vetorial.
DISTANCIA_MAXIMA_ACEITAVEL = 0.6

# Reranker: quantos candidatos buscar na primeira rodada (vetorial pura)
LIMITE_CANDIDATOS_RERANK = 15
# Reranker: quantos manter depois do rerank
LIMITE_FINAL = 7


def decidir_filtro(pergunta: str) -> str | None:
    """Decide se filtra por categoria. Mantenha leve — nao exaustivo."""
    pergunta_lower = pergunta.lower()

    if any(p in pergunta_lower for p in PALAVRAS_TOKENS):
        return "tokens"
    if any(p in pergunta_lower for p in PALAVRAS_COMPONENTES):
        return "componentes"

    return None


def _similaridade_cosseno(vetor_a: np.ndarray, vetor_b: np.ndarray) -> float:
    """Calcula similaridade de cosseno entre dois vetores (1 = identicos, 0 = ortogonais)."""
    norm_a = np.linalg.norm(vetor_a)
    norm_b = np.linalg.norm(vetor_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vetor_a, vetor_b) / (norm_a * norm_b))


def _rerankar(
    pergunta: str,
    modelo: SentenceTransformer,
    candidatos: list[dict[str, Any]],
    limite: int = LIMITE_FINAL,
) -> list[dict[str, Any]]:
    """
    Reranker simples: recalcula similaridade cosseno diretamente entre
    o vetor da pergunta e o vetor de cada chunk, reordenando por relevancia real.
    Mais preciso que a distancia do Oracle que pode usar indice aproximado (IVF).

    MELHORIA: boost por keyword — quando palavras da pergunta aparecem no
    nome do arquivo, componente, secao ou conteudo, aumenta a similaridade.
    Isso resolve casos de ambiguidade entre arquivos do mesmo tema.
    """
    if not candidatos:
        return []

    vetor_pergunta = modelo.encode(pergunta)

    # Gera embedding de cada candidato individualmente (mais preciso que batch)
    textos = [c.get("conteudo_embed", c["conteudo"]) for c in candidatos]
    vetores_candidatos = modelo.encode(textos)

    # Palavras da pergunta para boost (exclui stopwords curtas)
    palavras_pergunta = [p for p in pergunta.lower().split() if len(p) > 3]

    # Recalcula similaridade cosseno para cada par + boost por keyword
    for i, candidato in enumerate(candidatos):
        sim = _similaridade_cosseno(vetor_pergunta, vetores_candidatos[i])

        # Boost por keyword: +0.08 por palavra encontrada em metadados ou conteudo
        boost = 0.0
        texto_busca = " ".join([
            str(candidato.get("nome_arquivo", "")),
            str(candidato.get("componente", "")),
            str(candidato.get("secao", "")),
            candidato.get("conteudo", ""),
        ]).lower()

        for palavra in palavras_pergunta:
            if palavra in texto_busca:
                boost += 0.08

        # Limita boost maximo a 0.24 (3 palavras) para nao distorcer demais
        boost = min(boost, 0.24)

        candidato["distancia_bruta"] = 1.0 - sim  # SEM boost — usado só pra decisão de fora de escopo
        candidato["similaridade_rerank"] = min(1.0, sim + boost)
        candidato["distancia"] = 1.0 - candidato["similaridade_rerank"]  # COM boost — usado só pra ordenar

    # Ordena por similaridade decrescente
    candidatos_ordenados = sorted(candidatos, key=lambda x: x["similaridade_rerank"], reverse=True)

    return candidatos_ordenados[:limite]


def _buscar_por_keyword(
    conexao,
    pergunta: str,
    categoria: str | None,
    limite: int,
) -> list[dict[str, Any]]:
    """Fallback por keyword — usa bind variables, nunca concatena texto do
    usuario direto na string SQL (isso seria uma brecha de SQL injection).

    CORRECAO: agora busca tambem em nome_arquivo, componente e secao,
    permitindo que o usuario encontre chunks pelo nome do arquivo ou
    pelo componente associado.
    """
    cursor = conexao.cursor()
    palavras = [p for p in pergunta.lower().split() if len(p) > 3][:4]
    if not palavras:
        return []

    condicoes = []
    binds: dict[str, Any] = {}
    for i, p in enumerate(palavras):
        chave = f"palavra{i}"
        # Busca no conteudo, nome do arquivo, componente e secao
        condicoes.append(f"LOWER(conteudo) LIKE :{chave}")
        condicoes.append(f"LOWER(nome_arquivo) LIKE :{chave}")
        condicoes.append(f"LOWER(componente) LIKE :{chave}")
        condicoes.append(f"LOWER(secao) LIKE :{chave}")
        binds[chave] = f"%{p}%"

    likes = " OR ".join(condicoes)
    binds["limite"] = limite

    if categoria:
        binds["categoria"] = categoria
        sql = f"""
            SELECT id, conteudo, categoria, origem, componente, nome_arquivo,
                   secao, pagina, 0.0 as distancia
            FROM chunks_mosaic
            WHERE categoria = :categoria AND ({likes})
            FETCH FIRST :limite ROWS ONLY
        """
    else:
        sql = f"""
            SELECT id, conteudo, categoria, origem, componente, nome_arquivo,
                   secao, pagina, 0.0 as distancia
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
            "secao": row[6],
            "pagina": row[7],
            "distancia": row[8],
        })
    cursor.close()
    return resultados


def recuperar_contexto(pergunta: str, limite: int = LIMITE_FINAL) -> list[dict[str, Any]]:
    categoria = decidir_filtro(pergunta)
    conexao = conectar_oracle()

    try:
        modelo = carregar_modelo_embedding()

        # PASSO 1: Busca vetorial inicial (mais candidatos pro reranker)
        resultados_vetorial = buscar_similar(
            conexao=conexao,
            modelo=modelo,
            pergunta=pergunta,
            categoria=categoria,
            limite=LIMITE_CANDIDATOS_RERANK,
        )

        # PASSO 2: Reranker, recalcula similaridade com mais precisao + boost keyword
        resultados_vetorial = _rerankar(pergunta, modelo, resultados_vetorial, limite=LIMITE_CANDIDATOS_RERANK)
        for r in resultados_vetorial:
            r["origem_busca"] = "vetorial"

        # PASSO 3: Fallback por keyword se a busca vetorial nao trouxe nada ou trouxe resultados fracos
        melhor_distancia = resultados_vetorial[0]["distancia"] if resultados_vetorial else 999
        resultados_keyword = []
        if not resultados_vetorial or melhor_distancia > DISTANCIA_MAXIMA_ACEITAVEL:
            resultados_keyword = _buscar_por_keyword(conexao, pergunta, categoria, limite=5)
            for r in resultados_keyword:
                r["origem_busca"] = "keyword"

        # PASSO 4: Merge sem duplicatas, mantendo ordem do reranker
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

    print(f"\n[DEBUG RAG] Pergunta: '{pergunta}' | Filtro: {categoria} | Chunks: {len(resultados)}")
    for i, r in enumerate(resultados[:5], 1):
        amostra = r['conteudo'][:100].replace('\n', ' ')
        secao = f" [secao: {r.get('secao')}]" if r.get('secao') else ""
        pagina = f" [pag: {r.get('pagina')}]" if r.get('pagina') else ""
        print(f"  [{i}] {r['nome_arquivo']}{secao}{pagina} [{r['categoria']}] (dist: {r['distancia']:.4f}): {amostra}...")

    return resultados
