# ETAPA 2: Chunking por estrutura logica + fallback por tamanho com overlap
# Divide documentos em pedacos (chunks) com base em secoes/componentes,
# preservando metadados herdados do documento original.
# Fallback: quando nao ha estrutura clara, divide por tamanho fixo com overlap.

import re
from typing import Any

from pipeline.extracao import extrair_todos_documentos

# Tamanho maximo de chunk (em caracteres) para fallback por tamanho
TAMANHO_CHUNK = 800
# Sobreposicao entre chunks consecutivos (evita cortar ideia no meio)
OVERLAP_CHUNK = 150

# Sufixos de estado/variante em nome de token - lista pequena e estavel,
# ao contrario de uma lista de componentes que cresce sem parar.
SUFIXOS_VARIANTE_TOKEN = {
    "primary", "secondary", "tertiary", "danger", "success", "warning",
    "hover", "active", "disabled", "focus", "selected",
    "background", "border", "text", "icon",
}


def chunking_por_estrutura(documento: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Recebe um documento extraido e retorna uma lista de chunks.
    Cada chunk representa uma secao logica (titulo + paragrafos seguintes).
    Se nao houver estrutura clara, usa chunking por tamanho com overlap.
    """
    conteudo = documento["conteudo"]
    metadados_base = documento["metadados"].copy()

    # Se for JSON de tokens, cada paragrafo ja e um chunk independente
    if metadados_base.get("formato") == "json":
        return _chunking_json(conteudo, metadados_base)

    # Para Markdown e HTML, separa por titulos (#, ##, ###)
    if metadados_base.get("formato") in ("markdown", "html"):
        chunks = _chunking_por_titulos(conteudo, metadados_base)
        if len(chunks) > 1:
            return chunks
        # Se so gerou 1 chunk (documento sem titulos), cai no fallback por tamanho

    # Para PDF: cada pagina ja vem marcada como [Pagina N], usa isso
    if metadados_base.get("formato") == "pdf":
        chunks = _chunking_por_paginas(conteudo, metadados_base)
        if len(chunks) > 1:
            return chunks

    # CSV e outros: fallback por tamanho com overlap
    return _chunking_por_tamanho(conteudo, metadados_base)


def _componente_a_partir_do_token(nome_token: str) -> str | None:
    """
    Deriva o componente do slug do token removendo sufixos de estado do final.
    Ex: 'data-table-border' -> 'Data Table', 'button-primary-hover' -> 'Button'.
    Sem lista de componentes - escala junto com o resto do projeto.

    Limitacao conhecida: token generico nao ligado a um componente especifico
    (tipo 'spacing-05') tambem vira um "componente" (ex: 'Spacing') - falso
    positivo leve, nao quebra nada, so fica um pouco impreciso nesses casos.
    """
    partes = nome_token.split("-")
    while len(partes) > 1 and partes[-1] in SUFIXOS_VARIANTE_TOKEN:
        partes.pop()
    if not partes:
        return None
    return " ".join(partes).title()


def _chunking_json(conteudo: str, metadados: dict[str, Any]) -> list[dict[str, Any]]:
    """Cada frase de token vira um chunk separado para busca granular."""
    frases = [f.strip() for f in conteudo.split("\n\n") if f.strip()]
    chunks = []
    for frase in frases:
        # CORRECAO: .copy() para nao mutar o dict compartilhado entre chunks
        chunk = _criar_chunk(frase, metadados.copy())
        if frase.startswith("Token "):
            nome_token = frase.split("Token ")[1].split(" ")[0]
            componente = _componente_a_partir_do_token(nome_token)
            if componente:
                chunk["metadados"]["componente"] = componente
        chunks.append(chunk)
    return chunks


def _chunking_por_titulos(conteudo: str, metadados: dict[str, Any]) -> list[dict[str, Any]]:
    """Divide Markdown/HTML por titulos (#, ##, ###)."""
    linhas = conteudo.split("\n")
    chunks = []
    chunk_atual = {"titulo": "", "linhas": [], "secao": ""}

    for linha in linhas:
        linha_strip = linha.strip()

        if linha_strip.startswith("#"):
            if chunk_atual["linhas"]:
                texto = _montar_texto_chunk(chunk_atual)
                meta = metadados.copy()
                meta["secao"] = chunk_atual.get("secao", "")
                chunks.append(_criar_chunk(texto, meta))

            titulo = linha_strip.lstrip("#").strip()
            chunk_atual = {"titulo": titulo, "linhas": [linha_strip], "secao": titulo}
        else:
            chunk_atual["linhas"].append(linha)

    if chunk_atual["linhas"]:
        texto = _montar_texto_chunk(chunk_atual)
        meta = metadados.copy()
        meta["secao"] = chunk_atual.get("secao", "")
        chunks.append(_criar_chunk(texto, meta))

    return chunks


def _chunking_por_paginas(conteudo: str, metadados: dict[str, Any]) -> list[dict[str, Any]]:
    """Divide PDF por paginas (marcadas como [Pagina N])."""
    padrao_pagina = re.compile(r"\[Pagina\s*(\d+)\]\n(.*?)(?=\n\n\[Pagina\s*\d+\]|$)", re.DOTALL)
    chunks = []

    for match in padrao_pagina.finditer(conteudo):
        pagina_num = match.group(1)
        texto_pagina = match.group(2).strip()
        if texto_pagina:
            meta = metadados.copy()
            meta["pagina"] = pagina_num
            chunks.append(_criar_chunk(texto_pagina, meta))

    # Se nao achou padrao [Pagina N], cai no fallback por tamanho
    if not chunks:
        return _chunking_por_tamanho(conteudo, metadados)

    return chunks


def _chunking_por_tamanho(conteudo: str, metadados: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Fallback: divide o texto em chunks de tamanho fixo com overlap.
    Preserva metadados do documento original.
    """
    chunks = []
    inicio = 0
    tamanho = len(conteudo)

    while inicio < tamanho:
        fim = min(inicio + TAMANHO_CHUNK, tamanho)

        # Tenta nao cortar no meio de uma palavra: volta ate encontrar espaco ou nova linha
        if fim < tamanho:
            while fim > inicio and conteudo[fim] not in (" ", "\n"):
                fim -= 1
            if fim == inicio:  # nao achou espaco, corta no tamanho exato
                fim = min(inicio + TAMANHO_CHUNK, tamanho)

        trecho = conteudo[inicio:fim].strip()
        if trecho:
            chunks.append(_criar_chunk(trecho, metadados.copy()))

        inicio = fim - OVERLAP_CHUNK if fim < tamanho else fim

    return chunks


def _montar_texto_chunk(chunk: dict[str, Any]) -> str:
    """Junta as linhas do chunk e remove linhas vazias excessivas."""
    texto = "\n".join(chunk["linhas"]).strip()
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto


def _criar_chunk(conteudo: str, metadados: dict[str, Any]) -> dict[str, Any]:
    """
    Cria um chunk enriquecido com prefixo de metadados para o embedding.
    Repete o nome do arquivo para dar mais peso vetorial a ele,
    garantindo que buscas por nome de arquivo encontrem o chunk correto.
    """
    prefixos = []
    if metadados.get("nome_arquivo"):
        # Repete o nome do arquivo 2x para reforcar o peso no embedding
        prefixos.append(f"[Arquivo: {metadados['nome_arquivo']}]")
        prefixos.append(f"[Fonte: {metadados['nome_arquivo']}]")
    if metadados.get("componente"):
        prefixos.append(f"[Componente: {metadados['componente']}]")
    if metadados.get("categoria"):
        prefixos.append(f"[Categoria: {metadados['categoria']}]")
    if metadados.get("secao"):
        prefixos.append(f"[Secao: {metadados['secao']}]")

    conteudo_embed = " ".join(prefixos) + "\n\n" + conteudo if prefixos else conteudo

    return {
        "conteudo": conteudo,
        "conteudo_embed": conteudo_embed,
        "metadados": metadados,
    }


def gerar_todos_chunks() -> list[dict[str, Any]]:
    """Pipeline completo: extrai documentos e aplica chunking."""
    documentos = extrair_todos_documentos()
    todos_chunks = []

    for doc in documentos:
        chunks = chunking_por_estrutura(doc)
        todos_chunks.extend(chunks)

    print(f"[Chunking] Total de chunks gerados: {len(todos_chunks)}")
    return todos_chunks


# Script de teste rapido
if __name__ == "__main__":
    chunks = gerar_todos_chunks()
    for i, chunk in enumerate(chunks[:5], 1):
        print(f"\n--- Chunk {i} ---")
        print(f"Categoria: {chunk['metadados']['categoria']}")
        print(f"Componente: {chunk['metadados'].get('componente')}")
        print(f"Secao: {chunk['metadados'].get('secao')}")
        print(f"Pagina: {chunk['metadados'].get('pagina')}")
        print(f"Origem: {chunk['metadados']['origem']}")
        print(f"Conteudo ({len(chunk['conteudo'])} chars):")
        print(chunk["conteudo"][:300] + "...")
        print(f"Embed ({len(chunk['conteudo_embed'])} chars):")
        print(chunk["conteudo_embed"][:300] + "...")
