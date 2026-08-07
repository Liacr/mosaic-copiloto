# Interface principal do Mosaic, chat web com Streamlit.

import sys
import re
import uuid
from pathlib import Path

caminho_raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(caminho_raiz))

import streamlit as st

from app.componentes import (
    base_conhecimento,
    botao_auditoria_persistente,
    indicador_agente,
    menu_funcoes,
    upload_pdf_sidebar,
)
from grafo.grafo import grafo_mosaic


def inicializar_sessao():
    if "mensagens" not in st.session_state:
        st.session_state.mensagens = []
    if "processando" not in st.session_state:
        st.session_state.processando = False
    if "pergunta_para_processar" not in st.session_state:
        st.session_state.pergunta_para_processar = None
    if "codigo_para_processar" not in st.session_state:
        st.session_state.codigo_para_processar = None
    if "aguardando_upload" not in st.session_state:
        st.session_state.aguardando_upload = False
    if "pergunta_para_auditar" not in st.session_state:
        st.session_state.pergunta_para_auditar = ""
    if "feedbacks" not in st.session_state:
        st.session_state.feedbacks = {}
    if "pdf_texto" not in st.session_state:
        st.session_state.pdf_texto = None
    if "pdf_arquivo_nome" not in st.session_state:
        st.session_state.pdf_arquivo_nome = None


def adicionar_mensagem(papel: str, conteudo: str):
    msg = {
        "id": str(uuid.uuid4())[:8],
        "papel": papel,
        "conteudo": conteudo,
    }
    st.session_state.mensagens.append(msg)
    return msg["id"]


def _formatar_historico_para_prompt(mensagens: list[dict]) -> str:
    """Formata as últimas mensagens como histórico para o LLM."""
    if not mensagens:
        return ""
    linhas = []
    for msg in mensagens[-6:]:
        papel = "Usuário" if msg["papel"] == "usuario" else "Assistente"
        # Remove markdown de código pra não confundir o LLM
        conteudo = msg["conteudo"].replace("```css", "").replace("```", "").strip()
        linhas.append(f"{papel}: {conteudo}")
    return "\n".join(linhas)


def _renderizar_resposta_com_fontes(texto: str):
    """Separa o conteúdo principal das fontes e coloca as fontes em expander."""
    # Procura por "Fonte:" ou "Fontes:" no texto (com quebras de linha opcionais antes)
    padrao = re.compile(r"\n?\n?(?:Fonte|Fontes):\s*(.+)", re.DOTALL)
    match = padrao.search(texto)

    if not match:
        st.markdown(texto)
        return

    conteudo = texto[:match.start()].strip()
    fontes = match.group(0).strip()

    if conteudo:
        st.markdown(conteudo)

    with st.expander("📚 Fontes"):
        st.markdown(fontes)


def processar_pergunta(pergunta: str, codigo: str | None = None):
    historico = _formatar_historico_para_prompt(st.session_state.mensagens)
    estado_inicial = {
        "mensagens": [],
        "pergunta_atual": pergunta,
        "contextos": [],
        "resultado_auditoria": None,
        "oferecer_upload": False,
        "eh_saudacao": False,
        "codigo_para_auditar": codigo,
        "incluir_fontes": True,
        "historico": historico,
        "resposta_final": "",
        "contexto_pdf": st.session_state.get("pdf_texto"),
    }
    return grafo_mosaic.invoke(estado_inicial)


def main():
    st.set_page_config(
        page_title="Mosaic — Copiloto de Harmonia e Padronização",
        page_icon="🎨",
        layout="centered",
    )

    inicializar_sessao()

    st.title("🎨 Mosaic IA")
    indicador_agente()

    with st.sidebar:
        base_conhecimento()
        menu_funcoes()
        botao_auditoria_persistente()
        upload_pdf_sidebar()

    # Renderiza histórico
    for i, msg in enumerate(st.session_state.mensagens):
        with st.chat_message("user" if msg["papel"] == "usuario" else "assistant"):
            if msg["papel"] == "assistente":
                _renderizar_resposta_com_fontes(msg["conteudo"])
            else:
                st.markdown(msg["conteudo"])

            # CORREÇÃO: botão de feedback só nas respostas do assistente
            if msg["papel"] == "assistente":
                msg_id = msg["id"]
                feedback_atual = st.session_state.feedbacks.get(msg_id)
                cols = st.columns([1, 1, 8])
                with cols[0]:
                    if st.button("👍", key=f"up_{msg_id}_{i}", help="Resposta útil"):
                        st.session_state.feedbacks[msg_id] = "positivo"
                        st.toast("Obrigado pelo feedback! ✅")
                with cols[1]:
                    if st.button("👎", key=f"down_{msg_id}_{i}", help="Resposta não ajudou"):
                        st.session_state.feedbacks[msg_id] = "negativo"
                        st.toast("Feedback registrado. Vamos melhorar! ❌")
                if feedback_atual:
                    with cols[2]:
                        st.caption(f"Feedback: {feedback_atual}")

    # CICLO 2: Processa resposta pendente
    if st.session_state.processando and st.session_state.pergunta_para_processar:
        pergunta = st.session_state.pergunta_para_processar
        codigo = st.session_state.codigo_para_processar

        try:
            with st.chat_message("assistant"):
                with st.spinner("Consultando documentação..."):
                    resultado = processar_pergunta(pergunta, codigo=codigo)

                resposta = resultado.get("resposta_final", "Desculpe, não consegui processar sua pergunta.")
                _renderizar_resposta_com_fontes(resposta)

            adicionar_mensagem("assistente", resposta)
        except Exception as e:
            with st.chat_message("assistant"):
                st.error(f"Erro: {e}")
            adicionar_mensagem("assistente", f"Deu erro aqui: {e}. Tenta de novo?")
        finally:
            st.session_state.processando = False
            st.session_state.pergunta_para_processar = None
            st.session_state.codigo_para_processar = None

            # PDF é consulta pontual, some depois de UMA resposta, não
            # fica valendo pro resto da sessão (senão o bypass do
            # roteamento_pos_contexto continua ativo pra qualquer pergunta
            # seguinte, mesmo sem relação nenhuma com o PDF)
            if codigo is None and st.session_state.get("pdf_texto"):
                st.session_state.pdf_texto = None
                st.session_state.pdf_arquivo_nome = None

        st.rerun()

    # CICLO 1: Recebe input
    pergunta_sugerida = st.session_state.pop("pergunta_sugerida", None)
    pergunta = st.chat_input("Pergunte ao Mosaic sobre cores, componentes, ou cole um CSS pra auditar...")
    pergunta = pergunta_sugerida or pergunta

    if pergunta and not st.session_state.processando:
        # Se tiver PDF anexado, mostra indicador discreto na mensagem do usuário
        if st.session_state.get("pdf_arquivo_nome"):
            pergunta_com_pdf = f"{pergunta}\n\n*(📎 consultando com: {st.session_state.pdf_arquivo_nome})*"
        else:
            pergunta_com_pdf = pergunta

        adicionar_mensagem("usuario", pergunta_com_pdf)
        st.session_state.processando = True
        st.session_state.pergunta_para_processar = pergunta
        st.session_state.codigo_para_processar = None
        st.rerun()

    # Upload condicional, acionado só pelo botão fixo da sidebar
    if st.session_state.aguardando_upload:
        st.divider()
        st.markdown("**📎 Cole um trecho de código CSS para auditar:**")

        codigo_enviado = st.text_area(
            "Código CSS:",
            placeholder="Ex: .botao { background-color: #2979FF; padding: 20px; }",
            key="codigo_upload",
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            enviar = st.button("🔍 Auditar", type="primary")
        with col2:
            cancelar = st.button("❌ Cancelar")

        if cancelar:
            st.session_state.aguardando_upload = False
            st.rerun()

        if enviar and codigo_enviado.strip() and not st.session_state.processando:
            pergunta_original = st.session_state.pergunta_para_auditar
            codigo_fmt = f"```css\n{codigo_enviado.strip()}\n```"
            adicionar_mensagem("usuario", codigo_fmt)

            st.session_state.processando = True
            st.session_state.pergunta_para_processar = pergunta_original
            st.session_state.codigo_para_processar = codigo_enviado.strip()
            st.session_state.aguardando_upload = False
            st.rerun()


if __name__ == "__main__":
    main()
