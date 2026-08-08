# Widgets reutilizáveis da interface do Mosaic.

import streamlit as st


def indicador_agente():
    """Pitch curto do Mosaic — só o essencial."""
    st.markdown(
        """
        <div style="padding: 1rem 1.25rem; border-radius: 0.5rem;
                    background-color: rgba(15, 98, 254, 0.08); border-left: 4px solid #0f62fe;
                    margin-bottom: 1rem;">
            <p style="margin: 0; font-size: 0.95rem; line-height: 1.5;">
                🪄 <strong>Mosaic IA</strong> é o copiloto de Harmonia e Padronização de Produto da <strong>Mosaic Labs</strong>.
                Tira dúvidas sobre design system, audita seu CSS e avisa se você tá reinventando componente que já existe.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def base_conhecimento():
    """Lista o que o Mosaic tem na base — para consulta rápida na sidebar."""
    with st.expander("❓ O que o Mosaic IA conhece", expanded=False):
        st.markdown(
            """
            **Componentes Gerais**
            - Button, Input, Modal, Tag, Tooltip

            **Componentes internos Mosaic**
            - Data Table, Status Badge, Filter Bar, Empty State, Onboarding Tooltip

            **Tokens Carbon**
            - Cores e espaçamento

            **Tokens customizados Mosaic**
            - Paleta de marca (índigo, âmbar), tipografia Manrope, modo escuro

            **Documentação interna**
            - Guia CSS, checklist de acessibilidade, design system, etc...
            """
        )


def menu_funcoes():
    st.header("✨ Comece por aqui!")
    st.caption("Clique num exemplo, ou digite sua própria pergunta no chat")

    exemplos = [
        ("💬", "Já existe um componente de Tooltip?"),
        ("📊", "Como construo uma tabela de dados no padrão da Mosaic?"),
        ("🌙", "Quais cores usar no modo escuro?"),
    ]

    for icone, exemplo in exemplos:
        if st.button(f"{icone}  {exemplo}", key=f"exemplo_{exemplo[:15]}", use_container_width=True):
            st.session_state.pergunta_sugerida = exemplo
            st.rerun()

    st.caption("💡 Dica: digite 'oi' que eu me apresento!")


def botao_auditoria_persistente():
    """Porta de entrada fixa pra auditoria — sempre visível na sidebar,
    não depende de nenhuma resposta anterior ter tocado em token/componente."""
    st.divider()
    st.markdown("**🔍 Quer auditar um código agora?**")
    st.caption("Cole um trecho de CSS a qualquer momento, sem precisar perguntar antes")
    if st.button("Colar CSS para auditar", use_container_width=True, type="secondary"):
        st.session_state.aguardando_upload = True
        st.session_state.pergunta_para_auditar = "Audite este trecho de código CSS."
        st.rerun()


def upload_pdf_sidebar():
    """
    Upload de PDF na sidebar.

    CORRECAO: separa o estado do UPLOAD (persistente no sidebar) do estado
    da CONSULTA ATIVA (usado apenas na pergunta atual). Isso evita que o
    PDF "vaze" automaticamente para perguntas de follow-up depois de já
    ter sido consumido.

    Fluxo:
    1. Usuário faz upload → salva em pdf_uploaded_texto / pdf_uploaded_nome
    2. Usuário pergunta algo → interface.py copia para pdf_texto / pdf_arquivo_nome
    3. Resposta processada → finally limpa pdf_texto / pdf_arquivo_nome
    4. Próxima pergunta → NÃO mostra indicador do PDF (a menos que reative)
    """
    from pipeline.extracao import extrair_pdf_bytes
    from io import BytesIO

    st.divider()
    st.markdown("**🗂️ Anexar PDF**")
    st.caption("Anexe um PDF para consultar seu conteúdo.")

    arquivo = st.file_uploader("Escolha um PDF", type=["pdf"], key="pdf_upload_sidebar")

    # Estado do upload (persistente enquanto o arquivo estiver no uploader)
    if arquivo is not None:
        # Só extrai se mudou o arquivo
        if st.session_state.get("pdf_uploaded_nome") != arquivo.name:
            bytes_io = BytesIO(arquivo.getvalue())
            resultado = extrair_pdf_bytes(bytes_io, nome_arquivo=arquivo.name)
            if resultado:
                st.session_state.pdf_uploaded_texto = resultado["conteudo"]
                st.session_state.pdf_uploaded_nome = arquivo.name
                st.session_state.pdf_consumido = False  # marca como não consumido
                st.success(f"✅ {arquivo.name} anexado")
            else:
                st.error("❌ Não consegui extrair texto desse PDF.")
                st.session_state.pdf_uploaded_texto = None
                st.session_state.pdf_uploaded_nome = None
    else:
        # Usuário removeu o arquivo do uploader
        if st.session_state.get("pdf_uploaded_nome"):
            st.session_state.pdf_uploaded_texto = None
            st.session_state.pdf_uploaded_nome = None
            st.session_state.pdf_consumido = False
            # Limpa também o estado de consulta ativa, se existir
            st.session_state.pdf_texto = None
            st.session_state.pdf_arquivo_nome = None
            st.rerun()

    # CORRECAO: bloco único de markdown para evitar duplicação de captions
    # durante reruns do Streamlit (spinner, processamento, etc.)
    if st.session_state.get("pdf_uploaded_nome"):
        nome_pdf = st.session_state.pdf_uploaded_nome

        if st.session_state.get("pdf_consumido"):
            # PDF já foi consultado — mostra botão de reativar
            st.markdown(
                f"📄 **{nome_pdf}** pronto para consulta\n\n"
                f"> ✅ PDF já consultado. Use o botão abaixo para consultar novamente."
            )
            if st.button(
                "📎 Consultar PDF novamente",
                use_container_width=True,
                type="secondary",
                key="btn_reativar_pdf"
            ):
                st.session_state.pdf_consumido = False
                st.rerun()
        else:
            # PDF anexado e pronto para ser usado na próxima pergunta
            st.markdown(
                f"📄 **{nome_pdf}** pronto para consulta\n\n"
                f"> ℹ️ O PDF será usado na próxima pergunta\n"
                f"> 🗑️ Clique no ❌ do campo acima para remover o PDF"
            )
