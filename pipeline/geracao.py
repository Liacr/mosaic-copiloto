# ETAPA 5: Geracao da resposta
# 4 caminhos na auditoria: CONFORME / NAO CONFORME com oficial / SUGESTAO / NAO ACHOU

import time
from typing import Any

from google import genai
from google.genai.errors import ClientError

from config.settings import GEMINI_API_KEY, NOME_EMPRESA, NOME_PROJETO

cliente_gemini = genai.Client(api_key=GEMINI_API_KEY)
NOME_MODELO = "gemini-3.6-flash"


def chamar_gemini_com_retry(prompt: str, max_tentativas: int = 3) -> str:
    """Chama o Gemini com retry e backoff para rate limit (429)."""
    for tentativa in range(max_tentativas):
        try:
            resposta = cliente_gemini.models.generate_content(
                model=NOME_MODELO,
                contents=prompt,
            )
            return resposta.text
        except ClientError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                espera = (tentativa + 1) * 5
                print(f"[Gemini] Rate limit atingido. Aguardando {espera}s... (tentativa {tentativa + 1}/{max_tentativas})")
                time.sleep(espera)
            else:
                raise
    raise Exception("Max retries atingido para API do Gemini")


def gerar_saudacao() -> str:
    """Resposta de apresentacao. Chamada pelo grafo antes de qualquer busca vetorial."""
    return (
        f"E ai! Sou o **{NOME_PROJETO}**, copiloto de Harmonia e Padronizacao de Produto da **{NOME_EMPRESA}**. "
        f"To aqui pra te ajudar a nao reinventar a roda (ou o botao).\n\n"
        f"**O que posso fazer por voce:**\n"
        f"1. **Tirar duvidas** sobre tokens, componentes ou acessibilidade do Carbon\n"
        f"2. **Auditar codigo CSS** — manda o trecho que eu comparo com os tokens oficiais\n"
        f"3. **Consultar PDFs anexados** — envie um PDF na sidebar que eu respondo sobre o conteudo dele\n"
        f"4. **Descobrir se um componente ja existe** — descreve o que precisa que eu busco\n\n"
        f"Manda sua pergunta ou cole um codigo que eu te digo na hora!"
    )


def gerar_fora_de_escopo() -> str:
    """Recusa com personalidade. Chamada pelo grafo quando a busca nao acha nada relevante."""
    return (
        "Essa ai foge do meu radar! 😅 Eu so entendo de design system, componentes e "
        "padroes internos da Mosaic Labs. Se precisar de ajuda com token, componente ou "
        "um trecho de CSS, me chama que eu to aqui!"
    )


def construir_prompt(
    pergunta: str,
    contextos: list[dict[str, Any]],
    incluir_fontes: bool = False,
    historico: str = "",
    contexto_pdf: str | None = None,
) -> str:
    bloco_contexto = ""
    for i, ctx in enumerate(contextos, 1):
        fonte = ctx.get("nome_arquivo", "documento")
        comp = ctx.get("componente")
        if comp:
            fonte = f"{fonte} ({comp})"
        bloco_contexto += f"\n[{i}] {fonte}:\n{ctx['conteudo']}\n"

    instrucao_fontes = ""
    if incluir_fontes:
        instrucao_fontes = "No final, cite a fonte usada (nome do documento/token)."

    bloco_historico = ""
    if historico:
        bloco_historico = f"\nHISTORICO DA CONVERSA (contexto das mensagens anteriores):\n{historico}\n"

    bloco_pdf = ""
    regra_pdf = ""
    if contexto_pdf:
        # Trunca se for muito grande (limite de ~8000 chars pra nao estourar o prompt)
        pdf_truncado = contexto_pdf[:8000]
        if len(contexto_pdf) > 8000:
            pdf_truncado += "\n... (documento truncado por tamanho)"
        bloco_pdf = (
            f"\n---\n"
            f"DOCUMENTO PDF ANEXADO PELO USUARIO (consulta isolada):\n"
            f"{pdf_truncado}\n"
            f"---\n"
        )
        regra_pdf = (
            "REGRAS SOBRE O PDF ANEXADO:\n"
            "- Responda sobre o conteudo do PDF quando a pergunta for diretamente sobre ele.\n"
            "- NUNCA compare, cruze ou misture informacoes do PDF com a base oficial indexada.\n"
            "- NUNCA diga que algo do PDF 'bate' ou 'nao bate' com o design system da Mosaic.\n"
            "- Se o usuario pedir explicitamente para comparar o PDF com a base (ex: 'o PDF esta de acordo?'), "
            "recuse educadamente: 'Nao faco comparacoes automaticas entre documentos anexados e a base oficial. "
            "Se precisar de uma analise estruturada, recomendo falar com o Design Ops.'\n"
            "- O PDF e uma consulta isolada; a base oficial continua sendo a fonte de verdade para tokens e componentes.\n\n"
        )

    prompt = (
        f"Voce e o {NOME_PROJETO}, copiloto de Harmonia e Padronizacao de Produto da {NOME_EMPRESA}. "
        f"Tom: colega experiente, nao fiscal. Respostas curtas e diretas.\n\n"
        f"REGRAS ABSOLUTAS:\n"
        f"1. Responda SOMENTE com base nos contextos numerados abaixo. "
        f"Se a resposta nao estiver neles, diga que nao achou isso especificamente na documentacao "
        f"e sugira falar com o time de Design Ops — com suas proprias palavras, sem soar robotico.\n"
        f"2. NUNCA use conhecimento externo ou memoria de treino.\n"
        f"3. Seja breve — maximo 3 a 4 frases.\n"
        f"4. Se nao bater com o padrao: diz que nao bate, explica porque em 1 frase, e sugere o correto.\n"
        f"5. Se bate: confirma com um 'isso ai, ta certo' ou similar, sem alongar.\n"
        f"6. NUNCA se apresente como 'Sou o Mosaic' no meio da conversa.\n"
        f"7. {instrucao_fontes}\n"
        f"8. Se a pergunta fizer referencia a algo dito anteriormente (ex: 'e o secundario?'), use o historico da conversa.\n\n"
        f"{regra_pdf}"
        f"{bloco_historico}"
        f"CONTEXTO DISPONIVEL (sua unica fonte de verdade da base indexada):{bloco_contexto}\n"
        f"{bloco_pdf}"
        f"---\n"
        f"PERGUNTA DO COLEGA: {pergunta}\n"
        f"---\n"
        f"Responda em portugues do Brasil, como um colega experiente."
    )

    return prompt


def gerar_resposta(
    pergunta: str,
    contextos: list[dict[str, Any]],
    incluir_fontes: bool = False,
    historico: str = "",
    contexto_pdf: str | None = None,
) -> dict[str, Any]:
    prompt = construir_prompt(pergunta, contextos, incluir_fontes, historico, contexto_pdf)
    resposta = chamar_gemini_com_retry(prompt)
    return {"texto": resposta}


def gerar_resposta_com_auditoria(
    pergunta: str,
    contextos: list[dict[str, Any]],
    resultado_auditoria: dict[str, Any] | None,
    incluir_fontes: bool = False,
    historico: str = "",
    contexto_pdf: str | None = None,
) -> dict[str, Any]:
    """
    Arquitetura anti-hallucination: o LLM so escreve a frase de abertura.
    O veredito completo (tokens, valores, status) e montado 100% em Python.
    """
    from auditoria.comparador import montar_veredito_deterministico

    itens = resultado_auditoria.get("itens", []) if resultado_auditoria else []

    if not itens:
        return {"texto": "Nao recebi nenhum valor pra auditar nesse codigo."}

    linhas_veredito = [montar_veredito_deterministico(item) for item in itens]
    veredito_completo = "\n".join(linhas_veredito)

    prompt_tom = (
        f"Voce e o {NOME_PROJETO}, copiloto de Harmonia e Padronizacao de Produto da {NOME_EMPRESA}. "
        f"Escreva APENAS uma frase curta de abertura (sem numeros, sem nomes de token, sem valores hex) "
        f"pra introduzir um resultado de auditoria de codigo pro colega que perguntou: '{pergunta}'. "
        f"Tom: colega experiente, direto, sem enrolacao. So a frase de abertura, nada mais."
    )

    abertura = chamar_gemini_com_retry(prompt_tom)

    texto_final = f"{abertura.strip()}\n\n{veredito_completo}"
    return {"texto": texto_final}
