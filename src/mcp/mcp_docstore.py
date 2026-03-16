from mcp.server.fastmcp import FastMCP
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
vector_path = os.path.join(BASE_DIR, "vectors")

mcp = FastMCP("enem-docstore")

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    encode_kwargs={"normalize_embeddings": True}
)

db = Chroma(
    persist_directory=vector_path,
    embedding_function=embeddings
)

retriever = db.as_retriever(search_kwargs={"k": 3})

@mcp.tool()
def get_question(ano: int, numero: int):

    print(f"[MCP] get_question chamado → {ano} {numero}")

    resultado = db.get(
        where={
            "$and": [
                {"ano":    {"$eq": ano}},
                {"questao": {"$eq": numero}}
            ]
        },
        limit=1
    )

    if not resultado["ids"]:
        return {"page_content": "Questão não encontrada.", "metadata": {}}

    return {
        "page_content": resultado["documents"][0],
        "metadata":     resultado["metadatas"][0]
    }


@mcp.tool()
def get_similar_questions(query: str):

    docs = retriever.invoke(query)

    return [
        {
            "page_content": d.page_content,
            "metadata": d.metadata
        }
        for d in docs
    ]

if __name__ == "__main__":
    mcp.run()