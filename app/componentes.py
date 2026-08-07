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
    """Upload de PDF na sidebar — extrai texto na hora e guarda em session_state.
    O conteúdo vai como contexto extra na próxima pergunta, sem indexar no banco."""
    # Import lazy: só roda quando a função é chamada (sys.path já tá configurado pelo interface.py)
    from pipeline.extracao import extrair_pdf_bytes

    st.divider()
    st.markdown("**🗂️ Anexar PDF**")
    st.caption("Anexe um PDF para consultar seu conteúdo.")

    arquivo = st.file_uploader("Escolha um PDF", type=["pdf"], key="pdf_upload_sidebar")

    if arquivo is not None:
        # Extrai texto uma única vez, só quando muda o arquivo
        if st.session_state.get("pdf_arquivo_nome") != arquivo.name:
            from io import BytesIO
            bytes_io = BytesIO(arquivo.getvalue())
            resultado = extrair_pdf_bytes(bytes_io, nome_arquivo=arquivo.name)
            if resultado:
                st.session_state.pdf_texto = resultado["conteudo"]
                st.session_state.pdf_arquivo_nome = arquivo.name
                st.success(f"✅ {arquivo.name} anexado")
            else:
                st.error("❌ Não consegui extrair texto desse PDF.")
                st.session_state.pdf_texto = None
                st.session_state.pdf_arquivo_nome = None
    else:
        # Se o usuário limpou o uploader, limpa o estado também
        if st.session_state.get("pdf_arquivo_nome") and not arquivo:
            st.session_state.pdf_texto = None
            st.session_state.pdf_arquivo_nome = None
            st.rerun()

    if st.session_state.get("pdf_arquivo_nome"):
        st.caption(f"📄 {st.session_state.pdf_arquivo_nome} pronto para consulta")
        if st.button("🗑️ Limpar PDF", key="limpar_pdf"):
            st.session_state.pdf_texto = None
            st.session_state.pdf_arquivo_nome = None
            st.rerun()
