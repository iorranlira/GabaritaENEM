from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3"
)

db = Chroma(
    persist_directory="src/vectors",
    embedding_function=embeddings
)

retriever = db.as_retriever(search_kwargs={"k":5})

docs = retriever.invoke("questão sobre projeção ortogonal")

for d in docs:
   print("----")
   print(d.page_content)
   print(d.metadata)