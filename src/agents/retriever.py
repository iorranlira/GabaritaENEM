from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3"
)

db = Chroma(
    persist_directory="src/vectors",
    embedding_function=embeddings
)

retriever = db.as_retriever(search_kwargs={"k":3})

def retrieve_docs(query):    
    return retriever.invoke(query)