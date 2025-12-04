

import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


VECTORSTORE_DIR = "resume_index"
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def load_vectorstore():
    if os.path.exists(VECTORSTORE_DIR):
        print(" Loading existing FAISS vectorstore...")
        return FAISS.load_local(
            VECTORSTORE_DIR,
            embeddings=embedding_model,
            allow_dangerous_deserialization=True
        )

    else:
        print(" No vectorstore found.")
        return None

def create_vectorstore_from_docs(docs: list[Document]):
    print(" Creating new FAISS vectorstore...")
    vs = FAISS.from_documents(docs, embedding_model)
    vs.save_local(VECTORSTORE_DIR)
    return vs


