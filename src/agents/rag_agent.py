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

def supervisor_agent(question):

    prompt = ChatPromptTemplate.from_template("""
Você é um supervisor de um sistema que resolve questões do ENEM.

O banco de dados contém questões dos anos: 2010 a 2024.

Analise a pergunta abaixo e responda:

INVALIDA se:
- O ano mencionado não existe no banco (ex: 2047, 1999, 2027)
- O numero da questão não é entre 1 e 180 
- A pergunta não é sobre conteúdo ou resolução de questão do ENEM
- A pergunta é vaga demais (ex: "me explique o enem 2000")

VALIDA se:
- É uma pergunta sobre conteúdo de disciplina (ex: fotossíntese, entropia)
- Pede resolução de questão de um ano que existe no banco (2011-2025)

Pergunta: {question}

Responda apenas VALIDA ou INVALIDA.
""")

    chain = prompt | llm

    result = chain.invoke({"question": question}).content.strip()

    #if "INVALIDA" in result:
        #raise ValueError("Pergunta fora do escopo do sistema.")

    #return question
    return result

# Recupera uma questão especifica do banco de dados
def question_retriever_agent(question):

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
def similar_questions_agent(question):

    docs = retrieve_docs(question)

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


#def writer_agent(question_doc, similar_docs):

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

def writer_agent(question_doc, similar_docs):
    import re

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
        "gabarito": question_doc.metadata["gabarito"],
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