# ETAPA 5: Geração da resposta
# 4 caminhos na auditoria: CONFORME / NÃO CONFORME com oficial / SUGESTÃO / NÃO ACHOU

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
    """Resposta de apresentação. Chamada pelo grafo antes de qualquer busca vetorial."""
    return (
        f"E aí! Sou o **{NOME_PROJETO}**, copiloto de Harmonia e Padronização de Produto da **{NOME_EMPRESA}**. "
        f"To aqui pra te ajudar a não reinventar a roda (ou o botão).\n\n"
        f"**O que posso fazer por você:**\n"
        f"1. **Tirar dúvidas** sobre tokens, componentes ou acessibilidade do Carbon\n"
        f"2. **Auditar código CSS** — manda o trecho que eu comparo com os tokens oficiais\n"
        f"3. **Consultar PDFs anexados** — envie um PDF na sidebar que eu respondo sobre o conteúdo dele\n"
        f"4. **Descobrir se um componente já existe** — descreve o que precisa que eu busco\n\n"
        f"Manda sua pergunta ou cole um código que eu te digo na hora!"
    )


def gerar_fora_de_escopo() -> str:
    """Recusa com personalidade. Chamada pelo grafo quando a busca não acha nada relevante."""
    return (
        "Essa aí foge do meu radar! 😅 Eu só entendo de design system, componentes e "
        "padrões internos da Mosaic Labs. Se precisar de ajuda com token, componente ou "
        "um trecho de CSS, me chama que eu tô aqui!"
    )


def construir_prompt(
    pergunta: str,
    contextos: list[dict[str, Any]],
    incluir_fontes: bool = False,
    historico: str = "",
    contexto_pdf: str | None = None,
    contexto_pdf_nome: str | None = None,
) -> str:
    bloco_contexto = ""
    for i, ctx in enumerate(contextos, 1):
        fonte = ctx.get("nome_arquivo", "documento")
        comp = ctx.get("componente")
        secao = ctx.get("secao")
        pagina = ctx.get("pagina")

        partes_fonte = [fonte]
        if comp:
            partes_fonte.append(f"({comp})")
        if secao:
            partes_fonte.append(f"[secao: {secao}]")
        if pagina:
            partes_fonte.append(f"[pagina: {pagina}]")

        fonte_formatada = " ".join(partes_fonte)
        bloco_contexto += f"\n[{i}] {fonte_formatada}:\n{ctx['conteudo']}\n"

    instrucao_fontes = ""
    if incluir_fontes:
        instrucao_fontes = (
            "No final, cite a fonte usada. "
            "Use o formato: 'Fonte: nome_do_arquivo [secao: X]' ou 'Fonte: nome_do_arquivo [pagina: Y]'. "
            "Se não houver secao/pagina, cite só o nome do arquivo."
        )

    bloco_historico = ""
    if historico:
        bloco_historico = f"\nHISTÓRICO DA CONVERSA (contexto das mensagens anteriores):\n{historico}\n"

    bloco_pdf = ""
    regra_pdf = ""
    if contexto_pdf and contexto_pdf_nome:
        pdf_truncado = contexto_pdf[:8000]
        if len(contexto_pdf) > 8000:
            pdf_truncado += "\n... (documento truncado por tamanho)"
        bloco_pdf = (
            f"\n---\n"
            f"[PDF] {contexto_pdf_nome} (DOCUMENTO ANEXADO PELO USUÁRIO — CONSULTA ISOLADA):\n"
            f"{pdf_truncado}\n"
            f"---\n"
        )
        regra_pdf = (
            f"REGRAS SOBRE O PDF ANEXADO:\n"
            f"- Responda sobre o conteúdo do PDF quando a pergunta for diretamente sobre ele.\n"
            f"- NUNCA compare, cruze ou misture informações do PDF com a base oficial indexada.\n"
            f"- NUNCA diga que algo do PDF 'bate' ou 'não bate' com o design system da Mosaic.\n"
            f"- Se o usuário pedir explicitamente para comparar o PDF com a base, recuse educadamente.\n"
            f"- O PDF é uma consulta isolada; a base oficial continua sendo a fonte de verdade.\n"
            f"- Quando citar o PDF como fonte, use EXATAMENTE: 'Fonte: [PDF] {contexto_pdf_nome}'.\n\n"
        )

    prompt = (
        f"Você é o {NOME_PROJETO}, copiloto de Harmonia e Padronização de Produto da {NOME_EMPRESA}. "
        f"Tom: colega experiente, não fiscal. Respostas curtas e diretas.\n\n"
        f"REGRAS ABSOLUTAS:\n"
        f"1. Responda SOMENTE com base nos contextos numerados abaixo. "
        f"Se a resposta não estiver neles, diga que não achou isso especificamente na documentação "
        f"e sugira falar com o time de Design Ops — com suas próprias palavras, sem soar robótico.\n"
        f"2. NUNCA use conhecimento externo ou memória de treino.\n"
        f"3. Seja breve — máximo 3 a 4 frases.\n"
        f"4. Se não bater com o padrão: diz que não bate, explica porquê em 1 frase, e sugere o correto.\n"
        f"5. Se bate: confirma com um 'isso aí, tá certo' ou similar, sem alongar.\n"
        f"6. NUNCA se apresente como 'Sou o Mosaic' no meio da conversa.\n"
        f"7. {instrucao_fontes}\n"
        f"8. Se a pergunta fizer referência a algo dito anteriormente, use o histórico da conversa.\n\n"
        f"{regra_pdf}"
        f"{bloco_historico}"
        f"CONTEXTO DISPONÍVEL (sua única fonte de verdade da base indexada):{bloco_contexto}\n"
        f"{bloco_pdf}"
        f"---\n"
        f"PERGUNTA DO COLEGA: {pergunta}\n"
        f"---\n"
        f"Responda em português do Brasil, como um colega experiente."
    )

    return prompt


def gerar_resposta(
    pergunta: str,
    contextos: list[dict[str, Any]],
    incluir_fontes: bool = False,
    historico: str = "",
    contexto_pdf: str | None = None,
    contexto_pdf_nome: str | None = None,
) -> dict[str, Any]:
    prompt = construir_prompt(pergunta, contextos, incluir_fontes, historico, contexto_pdf, contexto_pdf_nome)
    resposta = chamar_gemini_com_retry(prompt)
    return {"texto": resposta}


def gerar_resposta_com_auditoria(
    pergunta: str,
    contextos: list[dict[str, Any]],
    resultado_auditoria: dict[str, Any] | None,
    incluir_fontes: bool = False,
    historico: str = "",
    contexto_pdf: str | None = None,
    contexto_pdf_nome: str | None = None,
) -> dict[str, Any]:
    from auditoria.comparador import montar_veredito_deterministico

    itens = resultado_auditoria.get("itens", []) if resultado_auditoria else []

    if not itens:
        return {"texto": "Não recebi nenhum valor pra auditar nesse código."}

    linhas_veredito = [montar_veredito_deterministico(item) for item in itens]
    veredito_completo = "\n".join(linhas_veredito)

    prompt_tom = (
        f"Você é o {NOME_PROJETO}, copiloto de Harmonia e Padronização de Produto da {NOME_EMPRESA}. "
        f"Escreva APENAS uma frase curta de abertura (sem números, sem nomes de token, sem valores hex) "
        f"pra introduzir um resultado de auditoria de código pro colega que perguntou: '{pergunta}'. "
        f"Tom: colega experiente, direto, sem enrolação. Só a frase de abertura, nada mais."
    )

    abertura = chamar_gemini_com_retry(prompt_tom)

    texto_final = f"{abertura.strip()}\n\n{veredito_completo}"
    return {"texto": texto_final}
