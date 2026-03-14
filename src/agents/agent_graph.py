from typing import TypedDict, List
from langgraph.graph import StateGraph, END

from rag_agent import (
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

def supervisor_node(state: AgentState):

    question = state["question"]

    supervisor_agent(question)

    return state


def question_retriever_node(state: AgentState):

    question = state["question"]

    doc = question_retriever_agent(question)

    return {
        "question_doc": doc
    }


def similar_retriever_node(state: AgentState):

    question = state["question"]

    docs = similar_questions_agent(question)

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

    doc = state["question_doc"]
    similar = state["similar_docs"]
    answer = state["answer"]

    context = doc.page_content + "\n".join(
        [d.page_content for d in similar]
    )

    safety_agent(context, answer)

    return state

def build_graph():

    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("question_retriever", question_retriever_node)
    graph.add_node("similar_retriever", similar_retriever_node)
    graph.add_node("writer", writer_node)
    graph.add_node("safety", safety_node)

    graph.set_entry_point("supervisor")

    graph.add_edge("supervisor", "question_retriever")
    graph.add_edge("question_retriever", "similar_retriever")
    graph.add_edge("similar_retriever", "writer")
    graph.add_edge("writer", "safety")
    graph.add_edge("safety", END)

    return graph.compile()