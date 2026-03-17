import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.agents.retriever import (retrieve_docs)
from src.agents.aux_def_rag import (parse_questao_enem)
from langchain_mcp_adapters.client import MultiServerMCPClient
import re
from langchain_core.documents import Document
import asyncio
from dotenv import load_dotenv
load_dotenv()


# LLM (Llama)
llm = ChatGroq(
    model="llama-3.1-8b-instant"
)

#server MCP local
client = MultiServerMCPClient(
    {
        "docstore": {
            "transport": "stdio",
            "command": "python",
            "args": ["src/mcp_server/mcp_docstore.py"]
        }
    }
)
tools = asyncio.run(client.get_tools())
tools = {tool.name: tool for tool in tools}

def supervisor_agent(question):

    prompt = ChatPromptTemplate.from_template("""
Você é um supervisor de um sistema que resolve questões do ENEM.

O banco de dados contém questões dos anos: 2011 a 2025.

Classifique a pergunta abaixo em UMA das três opções:

VALIDA    → pergunta sobre conteúdo de disciplina ou resolução de questão de um ano entre 2011 e 2025
SIMULADO  → pedido de geração de simulado, treino, lista ou conjunto de questões
INVALIDA  → ano fora do banco, número de questão fora de 1-180, pergunta vaga ou fora do escopo do ENEM

Exemplos SIMULADO:
- "gere um simulado de matemática"
- "quero treinar com questões de humanas"
- "me dê 5 questões de ciências da natureza"


Exemplos INVALIDA :
- O ano mencionado não existe no banco (ex: 2047, 1999, 2027)
- O numero da questão não é entre 1 e 180 
- A pergunta não é sobre conteúdo ou resolução de questão do ENEM
- A pergunta é vaga demais (ex: "me explique o enem 2000")

Exemplos VALIDA:
- É uma pergunta sobre conteúdo de disciplina (ex: fotossíntese, entropia)
- Pede resolução de questão de um ano que existe no banco (2011-2025)


Pergunta: {question}

Responda apenas: VALIDA, SIMULADO ou INVALIDA
""")

    chain = prompt | llm

    result = chain.invoke({"question": question}).content.strip()

    return result

async def question_retriever_agent(question):

    parsed = parse_questao_enem(question)

    if parsed:
        numero, ano = parsed

        doc_data = await tools["get_question"].ainvoke({
            "ano": ano,
            "numero": numero
        })

        #print("[AGENT] resposta MCP:", doc_data)

        if isinstance(doc_data, list) and doc_data:
            dado = json.loads(doc_data[0]["text"])

            if "page_content" in dado:
                return Document(
                    page_content=dado["page_content"],
                    metadata=dado["metadata"]
                )

    docs = retrieve_docs(question)

    if len(docs) == 0:
        raise ValueError("Nenhuma questão encontrada.")

    return docs[0]

async def similar_questions_agent(question):

    docs_data = await tools["get_similar_questions"].ainvoke({
        "query": question
    })

    #print("[DEBUG] tipo:", type(docs_data))
    #print("[DEBUG] conteudo:", docs_data)

    docs = []
    for item in docs_data:
        dado = json.loads(item["text"])
        docs.append(Document(
            page_content=dado["page_content"],
            metadata=dado["metadata"]
        ))

    similares = docs[1:]

    return similares


# Anti-alucinação
def safety_agent(context, answer):

    prompt = ChatPromptTemplate.from_template("""
Você é um verificador de consistência factual.

Contexto recuperado do banco de dados:
{context}

Resposta gerada pelo sistema:
{answer}

Verifique se TODAS as informações da resposta estão presentes no contexto.

Regras:
- Se a resposta usar informações que não aparecem no contexto, ela está incorreta.
- Se a resposta inventar fatos, ela está incorreta.

Responda apenas com uma palavra:

APROVADO
ou
REPROVADO
""")

    chain = prompt | llm

    result = chain.invoke({
        "context": context,
        "answer": answer
    }).content.strip().upper()

    return "APROVADO" in result


def writer_agent(question_doc, similar_docs):

    questao_texto = re.sub(r'\*?[A-Z]{2,}\d+[A-Za-z]+\d+\*?', '', question_doc.page_content).strip()

    similares_texto = "\n\n─────────────────────────────────────\n\n".join(
        [doc.page_content for doc in similar_docs]
    )

    prompt = ChatPromptTemplate.from_template("""
Você é um professor especialista no ENEM. Siga o formato abaixo À RISCA, sem inventar seções novas.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 QUESTÃO PRINCIPAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{questao}

▶ Gabarito: {gabarito}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EXPLICAÇÃO PEDAGÓGICA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 HABILIDADE AVALIADA
[escreva aqui em 2 frases qual competência da matriz do ENEM esta questão testa]

─────────────────────────────────────────

✅ POR QUE {gabarito} ESTÁ CORRETA
[explique diretamente por que esta alternativa responde à questão, usando o enunciado como evidência]

─────────────────────────────────────────

❌ POR QUE AS OUTRAS ESTÃO ERRADAS
[para cada alternativa que NÃO é {gabarito}, uma linha só:]

- [letra]: [erro conceitual em 1 frase direta]
- [letra]: [erro conceitual em 1 frase direta]
- [letra]: [erro conceitual em 1 frase direta]
- [letra]: [erro conceitual em 1 frase direta]

─────────────────────────────────────────

🪜 PASSO A PASSO
1. [como ler e interpretar o enunciado desta questão]
2. [como eliminar as alternativas erradas]
3. [como confirmar a alternativa {gabarito}]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 QUESTÕES SEMELHANTES PARA TREINO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{similares}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REGRAS ABSOLUTAS:
- Não repita o enunciado nas explicações
- Não explique nem dê gabarito das questões semelhantes
- Não crie seções além das listadas acima
- Substitua TODOS os colchetes [ ] por conteúdo real
""")

    chain = prompt | llm

    response = chain.invoke({
        "questao":  questao_texto,
        "gabarito":question_doc.metadata["gabarito"],
        "similares": similares_texto,
    })

    return response.content



def verificar_relevancia(question, docs):
    
    if not isinstance(docs, (list, tuple)):
        docs = [docs]
    docs = [d for d in docs if hasattr(d, "page_content")]
    
    if not docs:
        return False
 
    contexto = "\n\n---\n\n".join(d.page_content for d in docs)
 
    prompt = ChatPromptTemplate.from_template("""
Você é um avaliador rigoroso de relevância para um tutor de ENEM.

Pergunta do usuário:
{question}
 
Documentos recuperados:
{context}
 
Avalie se os documentos respondem ESPECIFICAMENTE à pergunta.
                                              
Exemplos de perguntas que devem ser IRRELEVANTE:
- Perguntas vagas como "me explique o ENEM 2000" ou "o que é o ENEM"
- Perguntas sobre anos sem questões no banco
- Perguntas que não são sobre conteúdo de nenhuma disciplina específica
- Perguntas fora do escopo de questões do ENEM

Só responda RELEVANTE se os documentos contiverem conteúdo que responde diretamente à dúvida do aluno sobre um conceito, tema ou questão específica.
Responda apenas:
RELEVANTE
ou
IRRELEVANTE
""")
 
    result = (prompt | llm).invoke({
        "question": question,
        "context": contexto
    }).content.strip().upper()
 
    return "RELEVANTE" in result