# ETAPA 1: Processamento e Extracao
# Converte cada formato de documento em texto limpo + metadados.
# JSON de tokens vira frases descritivas, nunca indexamos JSON bruto.

import csv
import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from config.settings import PASTA_CARBON, PASTA_INTERNOS

# Mapa explícito de arquivo -> categoria. Prioridade maxima: se o nome do
# arquivo esta aqui, a categoria e essa, ponto final.
# CORRECAO: adicionados todos os arquivos de componentes e documentacao
# para garantir reconhecimento deterministico por arquivo.
CATEGORIA_POR_ARQUIVO = {
    "componentes-internos.md": "componentes",
    "design-system-mosaic.md": "tokens",
    "padrao-css-frontend.md": "padrao-interno",
    "acessibilidade.md": "acessibilidade",
    "acessibilidade(1).md": "acessibilidade",
    "padrao_codigo.md": "padrao-interno",
    "guia_arquitetura.md": "padrao-interno",
    "planilha_ownership.csv": "ownership",
    "button.md": "componentes",
    "input.md": "componentes",
    "modal.md": "componentes",
    "tag.md": "componentes",
    "tooltip.md": "componentes",
    "tokens_cores.json": "tokens",
    "tokens_espacamento.json": "tokens",
}


def extrair_todos_documentos() -> list[dict[str, Any]]:
    """Varre carbon/ e internos/ e retorna lista plana de documentos."""
    documentos = []
    documentos.extend(_extrair_pasta(PASTA_INTERNOS, origem="interno-ficticio"))
    documentos.extend(_extrair_pasta(PASTA_CARBON, origem="carbon-oficial"))

    print(f"[Extracao] Total: {len(documentos)} documentos")
    print("[Extracao] Arquivo -> categoria (componente):")
    for doc in documentos:
        meta = doc["metadados"]
        print(f"  {meta['nome_arquivo']} -> {meta['categoria']} ({meta.get('componente')})")

    return documentos


def _extrair_pasta(caminho_pasta: Path, origem: str) -> list[dict[str, Any]]:
    documentos = []

    if not caminho_pasta.exists():
        print(f"[Extracao] Aviso: pasta nao encontrada: {caminho_pasta}")
        return documentos

    for caminho_arquivo in caminho_pasta.rglob("*"):
        if caminho_arquivo.is_dir() or caminho_arquivo.name.startswith("."):
            continue

        formato = caminho_arquivo.suffix.lower()
        documento = None

        if formato == ".md":
            documento = _extrair_markdown(caminho_arquivo, origem)
        elif formato == ".json":
            documento = _extrair_json(caminho_arquivo, origem)
        elif formato == ".csv":
            documento = _extrair_csv(caminho_arquivo, origem)
        elif formato == ".pdf":
            documento = _extrair_pdf(caminho_arquivo, origem)
        elif formato in (".html", ".htm"):
            documento = _extrair_html(caminho_arquivo, origem)
        else:
            print(f"[Extracao] Aviso: formato '{formato}' nao tratado, ignorando {caminho_arquivo.name}")

        if documento:
            documentos.append(documento)

    return documentos


def _extrair_markdown(caminho: Path, origem: str) -> dict[str, Any] | None:
    try:
        conteudo_bruto = caminho.read_text(encoding="utf-8")
    except Exception as erro:
        print(f"[Extracao] Erro ao ler {caminho}: {erro}")
        return None

    # Extrai frontmatter YAML (--- ... --- no inicio do arquivo)
    metadados_extras = _extrair_frontmatter(conteudo_bruto)
    conteudo = metadados_extras.pop("_conteudo_limpo", conteudo_bruto)

    categoria, componente = _detectar_categoria_e_componente(caminho, conteudo)

    # Se o frontmatter tiver categoria explicita, ela sobrescreve
    if "categoria" in metadados_extras:
        categoria = metadados_extras["categoria"]

    metadados = {
        "origem": origem,
        "categoria": categoria,
        "componente": componente,
        "nome_arquivo": caminho.name,
        "formato": "markdown",
        "data": metadados_extras.get("data"),
        "autor": metadados_extras.get("autor"),
        "secao": metadados_extras.get("secao"),
    }

    return {
        "conteudo": conteudo,
        "metadados": metadados,
    }


def _extrair_frontmatter(texto: str) -> dict[str, Any]:
    """Extrai frontmatter YAML do inicio do markdown. Retorna dict com os metadados + _conteudo_limpo."""
    if not texto.startswith("---"):
        return {"_conteudo_limpo": texto}

    partes = texto.split("---", 2)
    if len(partes) < 3:
        return {"_conteudo_limpo": texto}

    frontmatter = partes[1].strip()
    conteudo = partes[2].strip()
    resultado = {"_conteudo_limpo": conteudo}

    # Parser YAML minimalista (so chave: valor simples)
    for linha in frontmatter.split("\n"):
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            resultado[chave.strip()] = valor.strip()

    return resultado


def _extrair_json(caminho: Path, origem: str) -> dict[str, Any] | None:
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except Exception as erro:
        print(f"[Extracao] Erro ao ler JSON {caminho}: {erro}")
        return None

    categoria, componente = _detectar_categoria_e_componente(caminho, "")
    frases = _json_para_frases(dados, contexto="")
    conteudo = "\n\n".join(frases)

    return {
        "conteudo": conteudo,
        "metadados": {
            "origem": origem,
            "categoria": categoria,
            "componente": componente,
            "nome_arquivo": caminho.name,
            "formato": "json",
        },
    }


def _json_para_frases(dados: Any, contexto: str = "") -> list[str]:
    frases = []

    if isinstance(dados, dict):
        for chave, valor in dados.items():
            if isinstance(valor, dict) and "value" in valor:
                valor_token = valor.get("value", "")
                papel = valor.get("role", [])
                papel_texto = ", ".join(papel) if isinstance(papel, list) else str(papel)

                frase = (
                    f"Token {chave} do Carbon Design System, "
                    f"valor {valor_token}, "
                    f"usado em {papel_texto}."
                )
                frases.append(frase)

                for sub_chave, sub_valor in valor.items():
                    if sub_chave not in ("value", "role") and isinstance(sub_valor, (dict, list)):
                        frases.extend(_json_para_frases({sub_chave: sub_valor}, contexto=chave))

            elif isinstance(valor, (dict, list)):
                frases.extend(_json_para_frases(valor, contexto=chave))

    elif isinstance(dados, list):
        for item in dados:
            frases.extend(_json_para_frases(item, contexto=contexto))

    return frases


def _extrair_csv(caminho: Path, origem: str) -> dict[str, Any] | None:
    try:
        with caminho.open("r", encoding="utf-8", newline="") as arquivo:
            leitor = csv.DictReader(arquivo)
            linhas = list(leitor)
    except Exception as erro:
        print(f"[Extracao] Erro ao ler CSV {caminho}: {erro}")
        return None

    if not linhas:
        return None

    colunas = list(linhas[0].keys())
    frases = []
    for linha in linhas:
        partes = [f"{coluna}: {linha.get(coluna, '')}" for coluna in colunas if linha.get(coluna)]
        frases.append(" | ".join(partes))

    conteudo = "\n".join(frases)
    categoria, componente = _detectar_categoria_e_componente(caminho, conteudo)

    return {
        "conteudo": conteudo,
        "metadados": {
            "origem": origem,
            "categoria": categoria,
            "componente": componente,
            "nome_arquivo": caminho.name,
            "formato": "csv",
        },
    }


def _extrair_pdf(caminho: Path, origem: str) -> dict[str, Any] | None:
    try:
        from pypdf import PdfReader
    except ImportError:
        print(f"[Extracao] Aviso: pypdf nao instalado. Ignorando {caminho.name}")
        return None

    try:
        leitor = PdfReader(str(caminho))
        paginas = []
        for i, pagina in enumerate(leitor.pages, start=1):
            texto = pagina.extract_text()
            if texto:
                paginas.append(f"[Pagina {i}]\n{texto}")
        conteudo_bruto = "\n\n".join(paginas).strip()
    except Exception as erro:
        print(f"[Extracao] Erro ao ler PDF {caminho}: {erro}")
        return None

    if not conteudo_bruto:
        return None

    # LIMPEZA: remove cabecalhos/rodapes repetitivos e numeracao de pagina
    conteudo = _limpar_pdf(conteudo_bruto)

    categoria, componente = _detectar_categoria_e_componente(caminho, conteudo)
    return {
        "conteudo": conteudo,
        "metadados": {
            "origem": origem,
            "categoria": categoria,
            "componente": componente,
            "nome_arquivo": caminho.name,
            "formato": "pdf",
            "total_paginas": len(leitor.pages),
        },
    }


def _limpar_pdf(texto: str) -> str:
    """Remove ruídos comuns de PDFs: numeração de página, cabeçalhos/rodapés repetitivos.
    Mantém UMA linha em branco entre blocos, pra preservar a fronteira \n\n
    que o chunking por página depende."""
    linhas = texto.split("\n")
    linhas_limpas = []
    visto = set()

    for linha in linhas:
        linha_strip = linha.strip()

        if not linha_strip:
            # preserva no máximo 1 linha em branco seguida, nunca remove
            # a fronteira inteira, só evita acumular várias vazias
            if linhas_limpas and linhas_limpas[-1] != "":
                linhas_limpas.append("")
            continue

        if re.match(r"^(Pagina?\s*\d+|Page\s*\d+\s*(of|de)\s*\d+|\d+\s*/\s*\d+)$", linha_strip, re.IGNORECASE):
            continue

        if len(linha_strip.split()) <= 3 and linha_strip in visto:
            continue

        visto.add(linha_strip)
        linhas_limpas.append(linha_strip)

    return "\n".join(linhas_limpas)


def extrair_pdf_bytes(bytes_io: BytesIO, nome_arquivo: str = "upload.pdf", origem: str = "upload-usuario") -> dict[str, Any] | None:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("[Extracao] Aviso: pypdf nao instalado. Nao foi possivel extrair PDF.")
        return None

    try:
        leitor = PdfReader(bytes_io)
        paginas = []
        for i, pagina in enumerate(leitor.pages, start=1):
            texto = pagina.extract_text()
            if texto:
                paginas.append(f"[Pagina {i}]\n{texto}")
        conteudo_bruto = "\n\n".join(paginas).strip()
    except Exception as erro:
        print(f"[Extracao] Erro ao ler PDF bytes: {erro}")
        return None

    if not conteudo_bruto:
        return None

    conteudo = _limpar_pdf(conteudo_bruto)

    return {
        "conteudo": conteudo,
        "metadados": {
            "origem": origem,
            "categoria": "upload",
            "componente": None,
            "nome_arquivo": nome_arquivo,
            "formato": "pdf",
            "total_paginas": len(leitor.pages),
        },
    }


def _extrair_html(caminho: Path, origem: str) -> dict[str, Any] | None:
    try:
        html_bruto = caminho.read_text(encoding="utf-8")
    except Exception as erro:
        print(f"[Extracao] Erro ao ler HTML {caminho}: {erro}")
        return None

    sopa = BeautifulSoup(html_bruto, "html.parser")
    for tag_lixo in sopa(["script", "style"]):
        tag_lixo.decompose()

    conteudo = sopa.get_text(separator="\n\n")
    conteudo = re.sub(r"\n{3,}", "\n\n", conteudo).strip()

    categoria, componente = _detectar_categoria_e_componente(caminho, conteudo)

    return {
        "conteudo": conteudo,
        "metadados": {
            "origem": origem,
            "categoria": categoria,
            "componente": componente,
            "nome_arquivo": caminho.name,
            "formato": "html",
        },
    }


# Mapa de pasta -> categoria. Organize seus arquivos nestas pastas
# e o Mosaic detecta automaticamente, sem precisar editar codigo.
CATEGORIA_POR_PASTA = {
    "tokens": "tokens",
    "cores": "tokens",
    "colors": "tokens",
    "espacamento": "tokens",
    "spacing": "tokens",
    "tipografia": "tokens",
    "typography": "tokens",
    "componentes": "componentes",
    "components": "componentes",
    "acessibilidade": "acessibilidade",
    "accessibility": "acessibilidade",
    "a11y": "acessibilidade",
    "padroes": "padrao-interno",
    "padrao": "padrao-interno",
    "padrao-interno": "padrao-interno",
    "guia": "padrao-interno",
    "guia-interno": "padrao-interno",
    "arquitetura": "padrao-interno",
    "ownership": "ownership",
    "rh": "rh",
    "financeiro": "financeiro",
    "legal": "legal",
}


def _inferir_categoria_pela_pasta(caminho: Path) -> str | None:
    """Infere a categoria pela estrutura de pastas. Ex:
    dados/internos/componentes/card.md -> 'componentes'
    dados/carbon/tokens/cores.json -> 'tokens'
    """
    partes = [p.lower() for p in caminho.parts]
    for parte in reversed(partes):  # do arquivo ate a raiz
        if parte in CATEGORIA_POR_PASTA:
            return CATEGORIA_POR_PASTA[parte]
    return None


def _detectar_categoria_e_componente(caminho: Path, conteudo: str) -> tuple[str, str | None]:
    """
    CATEGORIA - hierarquia (mais confiavel pra menos confiavel):
    1. Mapa explicito de arquivo -> categoria
    2. Inferencia pela pasta do arquivo
    3. Pistas no nome do arquivo
    4. Adivinhacao pelo conteudo

    COMPONENTE - nunca usa lista fixa. Se a categoria for "componentes",
    o nome do componente E o proprio nome do arquivo (Title Case). Escala
    pra qualquer quantidade sem editar codigo - so nomear o arquivo certo
    dentro da pasta componentes/. Ex: data-table.md -> "Data Table".
    """
    nome = caminho.name.lower()
    texto = conteudo.lower()

    if caminho.name in CATEGORIA_POR_ARQUIVO:
        categoria = CATEGORIA_POR_ARQUIVO[caminho.name]
    else:
        categoria_pasta = _inferir_categoria_pela_pasta(caminho)
        if categoria_pasta:
            categoria = categoria_pasta
        else:
            if any(p in nome for p in ["token", "color", "spacing", "typography", "cores", "espacamento"]):
                categoria = "tokens"
            elif any(p in nome for p in ["accessibility", "a11y", "wcag"]):
                categoria = "acessibilidade"
            elif any(p in nome for p in ["padrao", "guia", "ownership", "arquitetura", "codigo"]):
                categoria = "padrao-interno"
            elif any(p in nome for p in ["componente", "component"]):
                categoria = "componentes"
            else:
                print(f"[Extracao] Aviso: '{caminho.name}' nao esta no mapa, nem na pasta, nem no nome — adivinhando pelo conteudo.")
                if any(p in texto for p in ["accessibility", "a11y", "wcag"]):
                    categoria = "acessibilidade"
                elif any(p in texto for p in ["padrao", "guia", "ownership", "arquitetura"]):
                    categoria = "padrao-interno"
                elif any(p in texto for p in ["token", "color", "spacing", "typography"]):
                    categoria = "tokens"
                else:
                    categoria = "componentes"

    componente = None
    if categoria == "componentes":
        componente = caminho.stem.replace("-", " ").replace("_", " ").title()

    return categoria, componente
