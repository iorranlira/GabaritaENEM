from agent_graph import build_graph
import asyncio 

graph = build_graph()

result = asyncio.run(graph.ainvoke({
    "question": "gere um simulado"
}))

print(result["answer"])