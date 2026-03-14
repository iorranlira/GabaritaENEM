from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from retriever import (retrieve_docs, db)
from aux_def_rag import (parse_questao_enem, retrieve_by_id)
from dotenv import load_dotenv
load_dotenv()


# LLM (Llama)
llm = ChatGroq(
    model="llama-3.1-8b-instant"
)

def supervisor_agent(question: str):

    prompt = ChatPromptTemplate.from_template("""
Você é um supervisor de um sistema que resolve questões do ENEM.

Analise a pergunta abaixo.

Pergunta:
{question}

Responda apenas:

VALIDA → se for uma questão ou pedido de resolução
INVALIDA → se for fora do escopo do ENEM
""")

    chain = prompt | llm

    result = chain.invoke({"question": question}).content.strip()

    if "INVALIDA" in result:
        raise ValueError("Pergunta fora do escopo do sistema.")

    return question

# Recupera uma questão especifica do banco de dados
def question_retriever_agent(question: str):

    parsed = parse_questao_enem(question)

    if parsed:
        numero, ano = parsed

        doc = retrieve_by_id(db, numero, ano)

        if doc:
            return doc

    docs = retrieve_docs(question)

    if len(docs) == 0:
        raise ValueError("Nenhuma questão encontrada.")

    return docs[0]


#  Recupera questões semelhantes do banco vetorial.
def similar_questions_agent(question: str):

    docs = retrieve_docs(question)

    similares = docs[1:]  

    return similares

# Anti-alucinação
def safety_agent(context: str, answer: str):

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
    }).content.strip()

    if "REPROVADO" in result:
        raise ValueError("Resposta possivelmente alucinada.")

    return True

def writer_agent(question_doc, similar_docs):

    questao_texto = question_doc.page_content

    similares_texto = "\n\n-----------------\n\n".join(
        [doc.page_content for doc in similar_docs]
    )

    prompt = ChatPromptTemplate.from_template("""
Você é um professor especialista em ENEM.

Primeiro mostre a **questão completa** exatamente como fornecida.

QUESTÃO PRINCIPAL
----------------
{questao}

Gabarito correto: {gabarito}

Depois explique pedagogicamente:

1) Qual habilidade/conceito da questão
2) Por que a alternativa correta está certa
3) Por que cada alternativa errada está incorreta
4) Por fim, Mostre o raciocínio passo a passo de resolução da questão

Depois apresente as **questões semelhantes para treino** exatamente como fornecidas:

{similares}

IMPORTANTE:
Não resuma nem reescreva as questões.
Mostre o enunciado e as alternativas completas.
na etapa de explicação: NÃO REPITA O ENUNCIADO QUANDO FOR EXPLICAR SE ELE ESTÁ CERTO OU ERRADO
comece dizendo qual é a correta e por que ela está correta, depois vá passando pelas alternativas erradas explicando por que estão erradas
Não explique, nem corrija, nem dê a alternativa correta as perguntas semelhantes de treino
""")

    chain = prompt | llm

    response = chain.invoke({
        "questao": questao_texto,
        "gabarito": question_doc.metadata["gabarito"],
        "similares": similares_texto
    })

    return response.content