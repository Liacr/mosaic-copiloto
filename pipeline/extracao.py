# ETAPA 1: Processamento e Extração
# Converte cada formato de documento em texto limpo + metadados.
# JSON de tokens vira frases descritivas, nunca indexamos JSON bruto.

import csv
import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from config.settings import PASTA_CARBON, PASTA_INTERNOS


def extrair_todos_documentos() -> list[dict[str, Any]]:
    """Varre carbon/ e internos/ e retorna lista plana de documentos."""
    documentos = []
    documentos.extend(_extrair_pasta(PASTA_INTERNOS, origem="interno-ficticio"))
    documentos.extend(_extrair_pasta(PASTA_CARBON, origem="carbon-oficial"))
    print(f"[Extracao] Total: {len(documentos)} documentos")
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
        elif formato in (".html", ".htm"):
            documento = _extrair_html(caminho_arquivo, origem)

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
    Heurística: nome do arquivo é mais confiável que o conteúdo.
    Categoria: prioridade absoluta pelo nome. Só olha o texto se o nome não der pista.
    Componente: conta quantos componentes diferentes aparecem. Se > 1, é documento geral (None).
    """
    nome = caminho.name.lower()
    texto = conteudo.lower()

    # CATEGORIA (prioridade: nome do arquivo)

    # Tokens: nome do arquivo é a pista mais forte
    if any(palavra in nome for palavra in ["token", "color", "spacing", "typography", "cores", "espacamento"]):
        categoria = "tokens"

    # Acessibilidade: só se o PRÓPRIO NOME do arquivo indicar isso
    elif any(palavra in nome for palavra in ["accessibility", "a11y", "wcag"]):
        categoria = "acessibilidade"

    # Padrão interno: nome do arquivo indica documentação interna da empresa
    elif any(palavra in nome for palavra in ["padrao", "guia", "ownership", "arquitetura", "codigo"]):
        categoria = "padrao-interno"

    # Componente específico: nome do arquivo tem o nome do componente
    elif any(comp in nome for comp in ["button", "input", "modal", "tooltip", "tag"]):
        categoria = "componentes"

    # Se o nome do arquivo não deu pista, aí sim consulta o conteúdo
    else:
        if any(palavra in texto for palavra in ["token", "color", "spacing", "typography"]):
            categoria = "tokens"
        elif any(palavra in texto for palavra in ["accessibility", "a11y", "wcag"]):
            categoria = "acessibilidade"
        elif any(palavra in texto for palavra in ["padrao", "guia", "ownership", "arquitetura"]):
            categoria = "padrao-interno"
        else:
            categoria = "componentes"

    # COMPONENTE (prioridade: nome do arquivo, depois contagem no texto)

    componentes_conhecidos = {
        "button": "Button",
        "input": "Input",
        "text field": "Input",
        "modal": "Modal",
        "tooltip": "Tooltip",
        "tag": "Tag",
    }

    # 1º: o nome do arquivo menciona um componente específico?
    componente_do_nome = None
    for chave, valor in componentes_conhecidos.items():
        if chave in nome:
            componente_do_nome = valor
            break

    if componente_do_nome:
        return categoria, componente_do_nome

    # 2º: conta quantos componentes diferentes aparecem no TEXTO
    componentes_encontrados = set()
    for chave, valor in componentes_conhecidos.items():
        if chave in texto:
            componentes_encontrados.add(valor)

    # Se encontrou exatamente 1 componente no texto → marca ele
    # Se encontrou 0 ou > 1 → é documento geral, marca None
    if len(componentes_encontrados) == 1:
        return categoria, componentes_encontrados.pop()

    return categoria, None