# Lê os documentos (md, json, csv, html) e devolve texto limpo + metadados pra cada um.

import csv
import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from config.settings import PASTA_CARBON, PASTA_INTERNOS


def extrair_todos_documentos() -> list[dict[str, Any]]:
    """Varre dados/carbon e dados/internos e extrai tudo que reconhece."""
    documentos = []

    documentos.extend(_extrair_pasta(PASTA_INTERNOS, origem="interno-ficticio"))
    documentos.extend(_extrair_pasta(PASTA_CARBON, origem="carbon-oficial"))

    print(f"[Extracao] Total de documentos extraídos: {len(documentos)}")
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
        elif formato == ".html" or formato == ".htm":
            documento = _extrair_html(caminho_arquivo, origem)

        if documento:
            documentos.append(documento)

    return documentos


def _extrair_markdown(caminho: Path, origem: str) -> dict[str, Any] | None:
    # mantem os titulos (#, ##) no texto de proposito, ajuda o chunking
    # a saber onde cada secao comeca
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
    # regra importante: nunca indexar o JSON cru como texto, o modelo de
    # embedding nao entende chave/valor separado -> converte pra frase antes
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
    """
    Transforma token em frase legivel.
    Ex: {"blue-60": {"value": "#0043CE", "role": ["button"]}}
        -> "Token blue-60 do Carbon Design System, valor #0043CE, usado em button."

    Precisa ser recursiva porque o JSON do Carbon tem token dentro de token
    (nao sabia disso de inicio, só percebi quando testei com o arquivo real).
    """
    frases = []

    if isinstance(dados, dict):
        for chave, valor in dados.items():
            if isinstance(valor, dict) and "value" in valor:
                valor_token = valor.get("value", "")
                papel = valor.get("role", [])
                papel_texto = ", ".join(papel) if isinstance(papel, list) else str(papel)

                frases.append(
                    f"Token {chave} do Carbon Design System, "
                    f"valor {valor_token}, usado em {papel_texto}."
                )

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
    # repete o nome da coluna em cada linha (tipo "categoria: tokens | responsavel: ...")
    # pra o embedding entender o que cada valor significa sozinho
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
        partes = []
        for coluna in colunas:
            valor = linha.get(coluna, "")
            if valor:
                partes.append(f"{coluna}: {valor}")
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
    nome = caminho.name.lower()
    texto = conteudo.lower()

    if "padrao" in nome or "guia" in nome or "ownership" in nome or "arquitetura" in nome:
        categoria_por_nome = "padrao-interno"
    elif "token" in nome or "color" in nome or "spacing" in nome or "typography" in nome:
        categoria_por_nome = "tokens"
    elif "accessibility" in nome or "a11y" in nome:
        categoria_por_nome = "acessibilidade"
    else:
        categoria_por_nome = None

    # so marca um componente especifico se so UM foi citado no documento.
    # se citar varios (tipo lista completa), e documento geral, deixa sem componente
    componentes_conhecidos = ["button", "input", "text field", "modal", "tooltip", "tag"]
    encontrados = [c for c in componentes_conhecidos if c in nome or c in texto]
    if len(encontrados) == 1:
        componente_detectado = encontrados[0].replace("text field", "Input").title()
    else:
        componente_detectado = None

    if categoria_por_nome:
        return categoria_por_nome, componente_detectado

    if "wcag" in texto:
        return "acessibilidade", componente_detectado

    if componente_detectado:
        return "componentes", componente_detectado

    return "componentes", componente_detectado