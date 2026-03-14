from agent_graph import build_graph

graph = build_graph()

result = graph.invoke({
    "question": "me explique a questão 1 do enem 2018"
})

print(result["answer"])