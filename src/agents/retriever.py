from langchain_community.vectorstores import Chroma
#from langchain_community.embeddings import HuggingFaceEmbeddings
from src.agents.embeddings import embeddings

db = Chroma(
    persist_directory="src/vectors",
    embedding_function=embeddings
)

retriever = db.as_retriever(search_kwargs={"k":3})

def retrieve_docs(query):    
    return retriever.invoke(query)