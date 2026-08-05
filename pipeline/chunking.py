# ETAPA 2: Chunking por estrutura lógica
# Divide documentos em pedaços (chunks) com base em seções/componentes,
# preservando metadados herdados do documento original.

from typing import Any

from pipeline.extracao import extrair_todos_documentos


def chunking_por_estrutura(documento: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Recebe um documento extraído e retorna uma lista de chunks.
    Cada chunk representa uma seção lógica (título + parágrafos seguintes).
    """
    conteudo = documento["conteudo"]
    metadados_base = documento["metadados"].copy()

    # Se for JSON de tokens, cada parágrafo já é um chunk independente
    if metadados_base.get("formato") == "json":
        return _chunking_json(conteudo, metadados_base)

    # Para Markdown e HTML, separa por títulos (#, ##, ###)
    if metadados_base.get("formato") in ("markdown", "html"):
        return _chunking_por_titulos(conteudo, metadados_base)

    # CSV e outros: um chunk só com o documento inteiro
    return [_criar_chunk(conteudo, metadados_base)]


COMPONENTES_CONHECIDOS = ["button", "input", "modal", "tooltip", "tag"]


def _chunking_json(conteudo: str, metadados: dict[str, Any]) -> list[dict[str, Any]]:
    """Cada frase de token vira um chunk separado para busca granular."""
    frases = [f.strip() for f in conteudo.split("\n\n") if f.strip()]
    chunks = []
    for frase in frases:
        chunk = _criar_chunk(frase, metadados)
        # Normaliza o prefixo do token para o mesmo padrão de componente do resto do sistema
        if frase.startswith("Token "):
            nome_token = frase.split("Token ")[1].split(" ")[0]
            prefixo = nome_token.split("-")[0]
            if prefixo in COMPONENTES_CONHECIDOS:
                chunk["metadados"]["componente"] = prefixo.title()
        chunks.append(chunk)
    return chunks


def _chunking_por_titulos(conteudo: str, metadados: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Divide Markdown/HTML por títulos (#, ##, ###).
    Cada chunk contém: título + todo o texto até o próximo título.
    """
    linhas = conteudo.split("\n")
    chunks = []
    chunk_atual = {"titulo": "", "linhas": []}

    for linha in linhas:
        linha_strip = linha.strip()

        # Detecta título Markdown (# Título, ## Subtítulo, ### Sub-subtítulo)
        if linha_strip.startswith("#"):
            # Salva o chunk anterior se tiver conteúdo
            if chunk_atual["linhas"]:
                texto = _montar_texto_chunk(chunk_atual)
                chunks.append(_criar_chunk(texto, metadados))

            # Inicia novo chunk com este título
            titulo = linha_strip.lstrip("#").strip()
            chunk_atual = {"titulo": titulo, "linhas": [linha_strip]}

        else:
            chunk_atual["linhas"].append(linha)

    # Não esquece o último chunk
    if chunk_atual["linhas"]:
        texto = _montar_texto_chunk(chunk_atual)
        chunks.append(_criar_chunk(texto, metadados))

    return chunks


def _montar_texto_chunk(chunk: dict[str, Any]) -> str:
    """Junta as linhas do chunk e remove linhas vazias excessivas."""
    texto = "\n".join(chunk["linhas"]).strip()
    # Remove múltiplas quebras de linha consecutivas
    import re
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto


def _criar_chunk(conteudo: str, metadados: dict[str, Any]) -> dict[str, Any]:
    return {
        "conteudo": conteudo,
        "metadados": metadados.copy(),
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


# Script de teste rápido
if __name__ == "__main__":
    chunks = gerar_todos_chunks()
    for i, chunk in enumerate(chunks[:5], 1):
        print(f"\n--- Chunk {i} ---")
        print(f"Categoria: {chunk['metadados']['categoria']}")
        print(f"Componente: {chunk['metadados'].get('componente')}")
        print(f"Origem: {chunk['metadados']['origem']}")
        print(f"Conteúdo ({len(chunk['conteudo'])} chars):")
        print(chunk["conteudo"][:300] + "...")