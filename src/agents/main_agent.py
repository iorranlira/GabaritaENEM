from agent_graph import build_graph

graph = build_graph()

result = graph.invoke({
    "question": "dado o ENEM 2022 me explique a Questão 42"
})

print(result["answer"])