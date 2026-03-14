import os
import json
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3"
)

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "processed"
VECTOR_DIR = str(ROOT_DIR / "src/vectors")


def carregar_jsons():

        documentos = []

        for arquivo in os.listdir(DATA_DIR):

            if not arquivo.endswith(".json"):
                continue

            caminho = os.path.join(DATA_DIR, arquivo)

            with open(caminho, "r", encoding="utf-8") as f:
                questoes = json.load(f)

            for q in questoes:

                alternativas = "\n".join(
                    [f"{k}) {v}" for k, v in q["alternativas"].items()]
                )

                texto = f"""
ENEM {q['ano']} - Questão {q['numero_questao']} - {q['area']}

{q['enunciado']}

Alternativas:
{alternativas}
"""

                doc = Document(
                    page_content=texto.strip(),
                    metadata={
                        "ano": q["ano"],
                        "area": q["area"],
                        "questao": q["numero_questao"],
                        "gabarito": q["gabarito"],
                        "source": arquivo
                    }
                )

                documentos.append(doc)

        return documentos


def criar_vector_store():

    docs = carregar_jsons()

    print(f"Total de documentos: {len(docs)}")

    db = Chroma.from_documents(
        docs,
        embedding=embeddings,
        persist_directory=VECTOR_DIR
    )

    db.persist()

    print("Vector store criado com sucesso!")


if __name__ == "__main__":
    criar_vector_store()