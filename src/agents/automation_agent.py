from logging import config
import random
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from pathlib import Path
import json
from rag_agent import llm

ROOT_DIR   = Path(__file__).resolve().parents[2]
VECTOR_DIR = str(ROOT_DIR / "src/vectors")

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

db = Chroma(
    persist_directory=VECTOR_DIR,
    embedding_function=embeddings,
)

AREAS_VALIDAS = {
    "linguagens":  "Linguagens, Códigos e suas Tecnologias",
    "humanas":     "Ciências Humanas e suas Tecnologias",
    "natureza":    "Ciências da Natureza e suas Tecnologias",
    "matematica":  "Matemática e suas Tecnologias"
}


def automation_agent(question):

    prompt = ChatPromptTemplate.from_template("""
Você é um assistente que interpreta pedidos de simulado do ENEM.

Áreas disponíveis:
- linguagens  → Linguagens, Códigos e suas Tecnologias
- humanas     → Ciências Humanas e suas Tecnologias
- natureza    → Ciências da Natureza e suas Tecnologias
- matematica  → Matemática e suas Tecnologias

Pedido do usuário:
{question}

Extraia as informações do pedido e responda APENAS neste formato JSON, sem explicações:
{{
  "areas": ["linguagens", "humanas"],
  "questoes_por_area": 3
}}

Regras:
- Se o usuário não especificar áreas, inclua todas as 4
- Se o usuário não especificar quantidade, use 3 por área
- questoes_por_area deve ser entre 1 e 10
""")

    chain = prompt | llm
    result = chain.invoke({"question": question}).content.strip()

    result = result.replace("```json", "").replace("```", "").strip()

    config = json.loads(result)
    return config



def buscar_questoes_por_area(area_chave, n):

    area_completa = AREAS_VALIDAS.get(area_chave)
    if not area_completa:
        return []

    query = f"questão sobre {area_completa}"

    docs = db.similarity_search(
        query,
        k=n * 3,  
        filter={"area": area_completa}
    )

    random.shuffle(docs)
    return docs[:n]


def montar_simulado(docs_por_area):
    linhas = []
    numero = 1

    for area, docs in docs_por_area.items():
        for doc in docs:
            meta = doc.metadata
            linhas.append(
                f"QUESTÃO {numero} — {meta.get('area', '')}\n"
                f"{doc.page_content}\n"
                f"─────────────────────────────────────"
            )
            numero += 1

    return "\n\n".join(linhas)


def automation_node(state):
    question = state["question"]

    print("[AUTOMATION] interpretando pedido...")

    try:
        config = automation_agent(question)
    except Exception as e:
        print(f"[AUTOMATION] erro ao interpretar pedido: {e}")
        return {
            **state,
            "answer":   "Não entendi o pedido de simulado. Tente: 'gere um simulado de matemática e humanas com 5 questões cada'.",
            "approved": False,
            "refuse":   True,
        }

    #areas  = config.get("areas", list(AREAS_VALIDAS.keys()))
    #n      = config.get("questoes_por_area", 3)

    areas = config.get("areas")

    # verifica se o usuário realmente citou alguma área
    usuario_citou_area = any(a in question.lower() for a in AREAS_VALIDAS)

    if not usuario_citou_area:
        areas = list(AREAS_VALIDAS.keys())

    # garante que só áreas válidas sejam usadas
    areas = [a for a in areas if a in AREAS_VALIDAS]

    if not areas:
        areas = list(AREAS_VALIDAS.keys())

    n = config.get("questoes_por_area", 3)






    print(f"[AUTOMATION] áreas: {areas} | {n} questões por área")

    docs_por_area = {}
    for area in areas:
        docs = buscar_questoes_por_area(area, n)
        if docs:
            docs_por_area[area] = docs
            print(f"[AUTOMATION] {area}: {len(docs)} questões encontradas")

    if not docs_por_area:
        return {
            **state,
            "answer":   "Não encontrei questões para as áreas solicitadas.",
            "approved": False,
            "refuse":   True,
        }

    print("[AUTOMATION] montando simulado...")
    simulado = montar_simulado(docs_por_area)

    total = sum(len(d) for d in docs_por_area.values())
    cabecalho = (
        f"📋 SIMULADO GERADO — {total} questões\n"
        f"Áreas: {', '.join(AREAS_VALIDAS[a] for a in docs_por_area)}\n"
        f"{'━' * 42}\n\n"
    )

    return {
        **state,
        "answer":   cabecalho + simulado,
        "approved": True,
        "refuse":   False,
    }