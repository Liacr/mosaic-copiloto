# ETAPA 1: Processamento e Extração
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

# Mapa explícito de arquivo -> categoria. Prioridade máxima: se o nome do
# arquivo está aqui, a categoria é essa, ponto final — nunca cai no
# adivinhador de texto, que é frágil (qualquer doc que MENCIONE a palavra
# "token" de passagem seria mal classificado).
CATEGORIA_POR_ARQUIVO = {
    "componentes-internos.md": "componentes",
    "design-system-mosaic.md": "design-system",
    "padrao-css-frontend.md": "padrao-interno",
    "acessibilidade.md": "acessibilidade",
    "padrao_codigo.md": "padrao-interno",
    "guia_arquitetura.md": "padrao-interno",
    "planilha_ownership.csv": "ownership",
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
        print(f"[Extracao] Aviso: pasta não encontrada: {caminho_pasta}")
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
            print(f"[Extracao] Aviso: formato '{formato}' não tratado, ignorando {caminho_arquivo.name}")

        if documento:
            documentos.append(documento)

    return documentos


def _extrair_markdown(caminho: Path, origem: str) -> dict[str, Any] | None:
    try:
        conteudo = caminho.read_text(encoding="utf-8")
    except Exception as erro:
        print(f"[Extracao] Erro ao ler {caminho}: {erro}")
        return None

    categoria, componente = _detectar_categoria_e_componente(caminho, conteudo)

    return {
        "conteudo": conteudo,
        "metadados": {
            "origem": origem,
            "categoria": categoria,
            "componente": componente,
            "nome_arquivo": caminho.name,
            "formato": "markdown",
        },
    }


def _extrair_json(caminho: Path, origem: str) -> dict[str, Any] | None:
    """Converte tokens JSON em frases descritivas, embedding entende linguagem natural, não chaves."""
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
    """Recursiva: transforma estrutura JSON em frases legíveis para embedding."""
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
    """Repete o cabeçalho em cada linha para o embedding entender o significado dos valores."""
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
    """Extrai texto de PDFs usando pypdf (a partir de arquivo no disco)."""
    try:
        from pypdf import PdfReader
    except ImportError:
        print(f"[Extracao] Aviso: pypdf não instalado. Ignorando {caminho.name}")
        return None

    try:
        leitor = PdfReader(str(caminho))
        paginas = []
        for pagina in leitor.pages:
            texto = pagina.extract_text()
            if texto:
                paginas.append(texto)
        conteudo = "\n\n".join(paginas).strip()
    except Exception as erro:
        print(f"[Extracao] Erro ao ler PDF {caminho}: {erro}")
        return None

    if not conteudo:
        return None

    categoria, componente = _detectar_categoria_e_componente(caminho, conteudo)
    return {
        "conteudo": conteudo,
        "metadados": {
            "origem": origem,
            "categoria": categoria,
            "componente": componente,
            "nome_arquivo": caminho.name,
            "formato": "pdf",
        },
    }


def extrair_pdf_bytes(bytes_io: BytesIO, nome_arquivo: str = "upload.pdf", origem: str = "upload-usuario") -> dict[str, Any] | None:
    """Extrai texto de PDF a partir de bytes (upload na interface, sem salvar em disco).
    Retorna o mesmo formato dos outros extratores: {conteudo, metadados}."""
    try:
        from pypdf import PdfReader
    except ImportError:
        print("[Extracao] Aviso: pypdf não instalado. Não foi possível extrair PDF.")
        return None

    try:
        leitor = PdfReader(bytes_io)
        paginas = []
        for pagina in leitor.pages:
            texto = pagina.extract_text()
            if texto:
                paginas.append(texto)
        conteudo = "\n\n".join(paginas).strip()
    except Exception as erro:
        print(f"[Extracao] Erro ao ler PDF bytes: {erro}")
        return None

    if not conteudo:
        return None

    return {
        "conteudo": conteudo,
        "metadados": {
            "origem": origem,
            "categoria": "upload",
            "componente": None,
            "nome_arquivo": nome_arquivo,
            "formato": "pdf",
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


def _detectar_categoria_e_componente(caminho: Path, conteudo: str) -> tuple[str, str | None]:
    """
    1º: nome do arquivo bate exatamente com o mapa explícito? Usa direto,
        sem adivinhação nenhuma.
    2º: só se o arquivo for desconhecido, tenta pelas pistas do nome.
    3º: só se nada no nome ajudar, tenta pelo conteúdo (menos confiável —
        por isso é o último recurso, não o primeiro).
    """
    nome = caminho.name.lower()
    texto = conteudo.lower()

    # 1º: mapa explícito — resolve de cara os documentos que já conhecemos
    if caminho.name in CATEGORIA_POR_ARQUIVO:
        categoria = CATEGORIA_POR_ARQUIVO[caminho.name]
    else:
        # 2º: pistas no nome do arquivo (só pra arquivo não mapeado)
        if any(p in nome for p in ["token", "color", "spacing", "typography", "cores", "espacamento"]):
            categoria = "tokens"
        elif any(p in nome for p in ["accessibility", "a11y", "wcag"]):
            categoria = "acessibilidade"
        elif any(p in nome for p in ["padrao", "guia", "ownership", "arquitetura", "codigo"]):
            categoria = "padrao-interno"
        elif any(comp in nome for comp in ["button", "input", "modal", "tooltip", "tag"]):
            categoria = "componentes"
        else:
            # 3º: último recurso, olha o conteúdo — sabendo que é impreciso
            print(f"[Extracao] Aviso: '{caminho.name}' não está no mapa nem tem pista no nome — adivinhando pelo conteúdo.")
            if any(p in texto for p in ["accessibility", "a11y", "wcag"]):
                categoria = "acessibilidade"
            elif any(p in texto for p in ["padrao", "guia", "ownership", "arquitetura"]):
                categoria = "padrao-interno"
            elif any(p in texto for p in ["token", "color", "spacing", "typography"]):
                categoria = "tokens"
            else:
                categoria = "componentes"

    # COMPONENTE (mesma lógica de antes: nome do arquivo primeiro, depois contagem no texto)
    componentes_conhecidos = {
        "button": "Button",
        "input": "Input",
        "text field": "Input",
        "modal": "Modal",
        "tooltip": "Tooltip",
        "tag": "Tag",
    }

    componente_do_nome = None
    for chave, valor in componentes_conhecidos.items():
        if chave in nome:
            componente_do_nome = valor
            break

    if componente_do_nome:
        return categoria, componente_do_nome

    componentes_encontrados = set()
    for chave, valor in componentes_conhecidos.items():
        if chave in texto:
            componentes_encontrados.add(valor)

    if len(componentes_encontrados) == 1:
        return categoria, componentes_encontrados.pop()

    return categoria, None
