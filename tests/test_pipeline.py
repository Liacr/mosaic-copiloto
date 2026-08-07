# Testes automatizados básicos com pytest.
# Rode com: pytest tests/test_pipeline.py -v

import sys
from pathlib import Path

caminho_raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(caminho_raiz))

from pipeline.extracao import extrair_todos_documentos, _detectar_categoria_e_componente
from pipeline.chunking import chunking_por_estrutura
from auditoria.comparador import extrair_valores_css, auditar_codigo


def test_extracao_encontra_documentos():
    docs = extrair_todos_documentos()
    assert len(docs) > 0, "Nenhum documento extraído"


def test_categoria_guia_arquitetura():
    from pathlib import Path
    cat, comp = _detectar_categoria_e_componente(
        Path("guia_arquitetura.md"), "documento sobre arquitetura"
    )
    assert cat == "padrao-interno"
    assert comp is None


def test_categoria_button():
    from pathlib import Path
    cat, comp = _detectar_categoria_e_componente(
        Path("button.md"), "# Button\nUse botões para ações."
    )
    assert cat == "componentes"
    assert comp == "Button"


def test_chunking_preserva_metadados():
    docs = extrair_todos_documentos()
    doc = [d for d in docs if d["metadados"]["nome_arquivo"] == "button.md"][0]
    chunks = chunking_por_estrutura(doc)
    assert len(chunks) > 0
    assert chunks[0]["metadados"]["categoria"] == "componentes"


def test_auditoria_extrai_cor_e_espacamento():
    css = ".botao { background-color: #2979FF; padding: 20px; }"
    valores = extrair_valores_css(css)
    assert len(valores) == 2
    assert valores[0]["tipo"] == "cor"
    assert valores[1]["tipo"] == "espacamento"


def test_auditoria_nao_conforme():
    css = ".botao { background-color: #2979FF; }"
    resultado = auditar_codigo(css, pergunta_original="Qual cor do botão?")
    assert resultado["conforme_geral"] is False
    assert resultado["itens"][0]["status"] == "NÃO CONFORME"