import re
import os
from langchain_core.documents import Document


def retrieve_by_id(db, numero, ano):

    results = db.get(
        where={
            "$and": [
                {"ano": ano},
                {"questao": numero}
            ]
        }
    )

    if results["documents"]:
        doc = Document(
            page_content=results["documents"][0],
            metadata=results["metadatas"][0]
        )
        return doc

    return None

def parse_questao_enem(texto):
    padrao1 = r"quest[aã]o\s*(\d+).*?enem\s*(?:de\s*)?(\d{4})"
    padrao2 = r"enem\s*(?:de\s*)?(\d{4}).*?quest[aã]o\s*(\d+)"
    
    match = re.search(padrao1, texto.lower())

    if match:
        numero = int(match.group(1))
        ano = int(match.group(2))
        return numero, ano

    match = re.search(padrao2, texto.lower())

    if match:
        ano = int(match.group(1))
        numero = int(match.group(2))
        return numero, ano

    return None
