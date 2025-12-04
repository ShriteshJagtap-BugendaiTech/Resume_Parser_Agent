from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import os
import json

# Path to store vector database
ENTITY_VECTORSTORE_DIR = "resume_entities_chatbot"

# Embedding model to use
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def create_entity_vectorstore2(entity_data: list[dict]):
    """
    Stores resume entities into FAISS vectorstore.
    Avoids duplicates based on 'source' filename.
    """
    print("Creating FAISS vectorstore for resume entities...")

    documents = []
    for item in entity_data:
        file_name = item["entities"].get("File", f"{item['file']}.pdf")
        content = json.dumps(item["entities"], indent=2)
        doc = Document(page_content=content, metadata={"source": file_name})
        documents.append(doc)

    if os.path.exists(ENTITY_VECTORSTORE_DIR):
        print("Appending to existing vectorstore...")
        vs = FAISS.load_local(
            ENTITY_VECTORSTORE_DIR,
            embeddings=embedding_model,
            allow_dangerous_deserialization=True
        )
        existing_sources = {
            d.metadata.get("source") for d in vs.docstore._dict.values()
        }

        new_docs = [doc for doc in documents if doc.metadata["source"] not in existing_sources]

        if not new_docs:
            print("No new documents to add.")
            return vs

        vs.add_documents(new_docs)
        vs.save_local(ENTITY_VECTORSTORE_DIR)
        return vs
    else:
        print("Creating new vectorstore...")
        vs = FAISS.from_documents(documents, embedding_model)
        vs.save_local(ENTITY_VECTORSTORE_DIR)
        return vs

def load_entity_vectorstore2():
    """
    Loads the entity vectorstore from disk, if it exists.
    """
    if os.path.exists(ENTITY_VECTORSTORE_DIR):
        print("Loading entity FAISS vectorstore...")
        return FAISS.load_local(
            ENTITY_VECTORSTORE_DIR,
            embeddings=embedding_model,
            allow_dangerous_deserialization=True
        )
    else:
        print("No entity vectorstore found.")

        return None
