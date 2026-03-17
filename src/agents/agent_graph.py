from typing import TypedDict, List
from unittest import result
from langgraph.graph import StateGraph, END
from src.agents.rag_agent import verificar_relevancia  
from src.agents.automation_agent import automation_node

from src.agents.rag_agent import (
    supervisor_agent,
    question_retriever_agent,
    similar_questions_agent,
    writer_agent,
    safety_agent
)


class AgentState(TypedDict):

    question: str
    question_doc: object
    similar_docs: List
    answer: str
    retry_count: int
    approved: bool  
    refuse: bool 
    simulado: bool

def supervisor_node(state: AgentState):

    question = state["question"]

    result = supervisor_agent(question)

    if "SIMULADO" in result:
        return {**state, "approved": False, "refuse": False, "simulado": True}
    
    if "INVALIDA" in result:
        return {**state, "approved": False, "refuse": True, "simulado": False}    
    
    return {**state, "approved": True, "refuse": False, "simulado": False}

async def question_retriever_node(state: AgentState):

    question = state["question"]

    doc = await question_retriever_agent(question)

    return {
        "question_doc": doc
    }


async def similar_retriever_node(state: AgentState):

    question = state["question"]

    docs = await similar_questions_agent(question)

    return {
        "similar_docs": docs
    }


def writer_node(state: AgentState):

    doc = state["question_doc"]
    similar = state["similar_docs"]

    answer = writer_agent(doc, similar)

    return {
        "answer": answer
    }


def safety_node(state: AgentState):

    question = state["question"]
    doc = state["question_doc"]
    similar = state["similar_docs"]
    answer = state["answer"]
    retry = state.get("retry_count", 0)
    
    docs_relevantes = verificar_relevancia(question, doc)
    
    if not docs_relevantes:
        print(f"[SAFETY] documentos irrelevantes (tentativa {retry + 1})")
        if retry < 1:
            return {**state, "retry_count": retry + 1, "approved": False, "refuse": False}
        else:
            print("[SAFETY] re-busca esgotada -> recusando")
            return {**state, "approved": False, "refuse": True}
    
    
    context = doc.page_content + "\n\n".join(
        [d.page_content for d in similar]
    )

    resposta = safety_agent(context, answer)

    if not resposta:
        print(f"[SAFETY] alucinacao detectada (tentativa {retry + 1})")
        if retry < 1:
            return {**state, "retry_count": retry + 1, "approved": False, "refuse": False}
        else:
            print("[SAFETY] re-busca esgotada -> recusando")
            return {**state, "approved": False, "refuse": True}

    return {**state, "approved": True, "refuse": False}


def safety_route(state):
    if state.get("approved"):
        return "resposta_final"
    if state.get("refuse"):
        return "recusar"
    return "recuperador"

def recusar_node(state):
    return {**state, "answer": "\n \n Não foi possível encontrar evidências suficientes para responder com segurança. Tente reformular sua pergunta."}


def resposta_final_node(state):
    return state

def supervisor_router(state):

    if state.get("refuse"):
        return "recusar"
    if state.get("simulado"): 
        return "automation"
    
    return "question_retriever"


def build_graph():

    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("question_retriever", question_retriever_node)
    graph.add_node("similar_retriever", similar_retriever_node)
    graph.add_node("writer", writer_node)
    graph.add_node("safety", safety_node)
    graph.add_node("resposta_final",      resposta_final_node)
    graph.add_node("recusar",             recusar_node)
    graph.add_node("automation", automation_node)
    
    graph.set_entry_point("supervisor")

    graph.add_conditional_edges("supervisor", supervisor_router,
        {
            "question_retriever": "question_retriever",
            "recusar": "recusar",
            "automation": "automation"
        }
    )

    graph.add_edge("question_retriever", "similar_retriever")
    graph.add_edge("similar_retriever", "writer")
    graph.add_edge("writer", "safety")

    graph.add_conditional_edges("safety", safety_route, {
        "resposta_final": "resposta_final",
        "recusar":        "recusar",
        "recuperador":    "question_retriever",  
    })

    graph.add_edge("automation", "resposta_final")
    graph.add_edge("resposta_final", END)
    graph.add_edge("recusar",        END)

    return graph.compile()