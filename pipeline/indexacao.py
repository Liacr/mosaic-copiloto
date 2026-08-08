# ETAPA 3: Indexacao Vetorial
# Singleton para o modelo de embedding (carrega uma unica vez).

import array
import uuid
from typing import Any

import oracledb
from sentence_transformers import SentenceTransformer

from config.settings import (
    DIMENSAO_VETOR,
    MODELO_EMBEDDING,
    ORACLE_DSN,
    ORACLE_PASSWORD,
    ORACLE_USER,
    ORACLE_WALLET_PASSWORD,
    PASTA_WALLET,
)
from pipeline.chunking import gerar_todos_chunks

# Singleton: modelo carregado uma unica vez na primeira chamada
_modelo_embedding: SentenceTransformer | None = None


def carregar_modelo_embedding() -> SentenceTransformer:
    """Carrega o modelo uma unica vez (singleton)."""
    global _modelo_embedding
    if _modelo_embedding is None:
        print(f"[Indexacao] Carregando modelo {MODELO_EMBEDDING}...")
        _modelo_embedding = SentenceTransformer(MODELO_EMBEDDING)
        print("[Indexacao] Modelo carregado e em memoria.")
    return _modelo_embedding


def conectar_oracle() -> oracledb.Connection:
    return oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=ORACLE_DSN,
        config_dir=str(PASTA_WALLET),
        wallet_location=str(PASTA_WALLET),
        wallet_password=ORACLE_WALLET_PASSWORD,
    )


def criar_tabela_chunks(conexao: oracledb.Connection) -> None:
    cursor = conexao.cursor()
    # Dropa a tabela se existir (garante que a estrutura esteja sempre atualizada)
    try:
        cursor.execute("DROP TABLE chunks_mosaic")
        conexao.commit()
        print("[Indexacao] Tabela antiga removida.")
    except oracledb.DatabaseError as e:
        if "ORA-00942" in str(e):  # table does not exist
            pass
        else:
            raise

    sql_criar = f"""
        CREATE TABLE chunks_mosaic (
            id              VARCHAR2(36) PRIMARY KEY,
            conteudo        CLOB NOT NULL,
            embedding       VECTOR({DIMENSAO_VETOR}, FLOAT32),
            categoria       VARCHAR2(50),
            origem          VARCHAR2(50),
            componente      VARCHAR2(50),
            nome_arquivo    VARCHAR2(200),
            formato         VARCHAR2(20),
            secao           VARCHAR2(200),
            pagina          NUMBER,
            data_doc        VARCHAR2(20),
            autor           VARCHAR2(100)
        )
    """
    cursor.execute(sql_criar)
    conexao.commit()
    cursor.close()
    print("[Indexacao] Tabela chunks_mosaic criada com sucesso.")


def criar_indices(conexao: oracledb.Connection) -> None:
    """Cria indices para busca eficiente: vetorial (IVF) e em metadados."""
    cursor = conexao.cursor()

    # Indice IVF no vetor para busca aproximada rapida
    try:
        cursor.execute(f"""
            CREATE VECTOR INDEX idx_chunks_embedding ON chunks_mosaic(embedding)
            ORGANIZATION NEIGHBOR PARTITIONS
            DISTANCE COSINE
            WITH TARGET ACCURACY 95
        """)
        conexao.commit()
        print("[Indexacao] Indice vetorial IVF criado.")
    except oracledb.DatabaseError as e:
        if "ORA-00955" in str(e) or "ORA-02303" in str(e):
            print("[Indexacao] Indice vetorial ja existe.")
        else:
            print(f"[Indexacao] Aviso: nao foi possivel criar indice IVF: {e}")
            print("[Indexacao] A busca vetorial continuara funcionando (sem indice aproximado).")

    # Indice tradicional na categoria para filtragem rapida
    try:
        cursor.execute("CREATE INDEX idx_chunks_categoria ON chunks_mosaic(categoria)")
        conexao.commit()
        print("[Indexacao] Indice em categoria criado.")
    except oracledb.DatabaseError as e:
        if "ORA-00955" in str(e):
            print("[Indexacao] Indice em categoria ja existe.")
        else:
            raise

    cursor.close()


def limpar_tabela_chunks(conexao: oracledb.Connection) -> None:
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM chunks_mosaic")
    conexao.commit()
    cursor.close()
    print("[Indexacao] Tabela limpa.")


def indexar_chunks(
    conexao: oracledb.Connection,
    modelo: SentenceTransformer,
    chunks: list[dict[str, Any]],
) -> None:
    cursor = conexao.cursor()
    sql_inserir = """
        INSERT INTO chunks_mosaic (
            id, conteudo, embedding, categoria, origem, componente, nome_arquivo,
            formato, secao, pagina, data_doc, autor
        ) VALUES (
            :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12
        )
    """

    # CORRECAO: usa conteudo_embed para embedding, mas salva conteudo original no banco
    textos = [chunk.get("conteudo_embed", chunk["conteudo"]) for chunk in chunks]
    print(f"[Indexacao] Gerando embeddings para {len(textos)} chunks...")
    embeddings = modelo.encode(textos, show_progress_bar=True)

    registros = []
    for chunk, vetor in zip(chunks, embeddings):
        meta = chunk["metadados"]
        registros.append((
            str(uuid.uuid4()),
            chunk["conteudo"],
            array.array("f", vetor.tolist()),
            meta.get("categoria"),
            meta.get("origem"),
            meta.get("componente"),
            meta.get("nome_arquivo"),
            meta.get("formato"),
            meta.get("secao"),
            meta.get("pagina"),
            meta.get("data"),
            meta.get("autor"),
        ))

    tamanho_batch = 100
    for i in range(0, len(registros), tamanho_batch):
        lote = registros[i : i + tamanho_batch]
        cursor.executemany(sql_inserir, lote)
        conexao.commit()
        print(f"[Indexacao] Inseridos {min(i + tamanho_batch, len(registros))}/{len(registros)}")

    cursor.close()
    print("[Indexacao] Indexacao completa.")


def buscar_similar(
    conexao: oracledb.Connection,
    modelo: SentenceTransformer,
    pergunta: str,
    categoria: str | None = None,
    limite: int = 5,
) -> list[dict[str, Any]]:
    vetor_pergunta = modelo.encode(pergunta)
    vetor_bind = array.array("f", vetor_pergunta.tolist())

    cursor = conexao.cursor()

    if categoria:
        sql = """
            SELECT id, conteudo, categoria, origem, componente, nome_arquivo,
                   secao, pagina, data_doc, autor,
                   COSINE_DISTANCE(embedding, :vetor) as distancia
            FROM chunks_mosaic
            WHERE categoria = :categoria
            ORDER BY COSINE_DISTANCE(embedding, :vetor)
            FETCH FIRST :limite ROWS ONLY
        """
        cursor.execute(sql, {"vetor": vetor_bind, "categoria": categoria, "limite": limite})
    else:
        sql = """
            SELECT id, conteudo, categoria, origem, componente, nome_arquivo,
                   secao, pagina, data_doc, autor,
                   COSINE_DISTANCE(embedding, :vetor) as distancia
            FROM chunks_mosaic
            ORDER BY COSINE_DISTANCE(embedding, :vetor)
            FETCH FIRST :limite ROWS ONLY
        """
        cursor.execute(sql, {"vetor": vetor_bind, "limite": limite})

    resultados = []
    for row in cursor:
        conteudo = row[1]
        if hasattr(conteudo, "read"):
            conteudo = conteudo.read()

        resultados.append({
            "id": row[0],
            "conteudo": conteudo,
            "categoria": row[2],
            "origem": row[3],
            "componente": row[4],
            "nome_arquivo": row[5],
            "secao": row[6],
            "pagina": row[7],
            "data_doc": row[8],
            "autor": row[9],
            "distancia": row[10],
        })

    cursor.close()
    return resultados


def executar_indexacao_completa() -> None:
    chunks = gerar_todos_chunks()
    conexao = conectar_oracle()
    try:
        criar_tabela_chunks(conexao)
        modelo = carregar_modelo_embedding()
        indexar_chunks(conexao, modelo, chunks)
        criar_indices(conexao)
    finally:
        conexao.close()
        print("[Indexacao] Conexao fechada.")


if __name__ == "__main__":
    executar_indexacao_completa()
