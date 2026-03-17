from src.agents.agent_graph import build_graph
import asyncio 
graph = build_graph()

print("""══════════════════════════════════════════
🤖 GabaritaENEM - AI Student Assistant
══════════════════════════════════════════

O que posso fazer:

📚 Buscar e resolver questões do ENEM
📝 Gerar simulados personalizados
🔎 Encontrar questões semelhantes
""")

while True: 
    question = input("> Digite sua pergunta: ")
    print()

    # if question.lower() in ["sair", "exit", "quit"]:
    #     print("👋 Até logo!")
    #     break

    result = asyncio.run(graph.ainvoke({
        "question": question
    }))

    print(result["answer"])
    print("\n────────────────────────────────────────")

    continuar = input("Posso ajudar em outra coisa? (s/n): ")
    print()

    if continuar.lower() not in ["s", "sim", "y", "yes"]:
        print("👋 Até logo!")
        break