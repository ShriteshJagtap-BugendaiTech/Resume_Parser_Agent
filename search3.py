import os
import json
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain.schema import Document, HumanMessage
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
# === Import external agents ===
from chatbot_main import resume_chat_agent
from rag_main import invoke_with_fallback, thread_id
from vectorstore1 import load_entity_vectorstore   
from vectorstore2 import load_entity_vectorstore2  
import html
import streamlit as st
os.environ['GROQ_API_KEY'] = st.secrets["GROQ_API_KEY"]
# === LLM setup ===
llm = ChatGroq(model_name="llama-3.3-70b-versatile", api_key=st.secrets["GROQ_API_KEY"])
ollama_llm = ChatOllama(model="llama3.2:1b-instruct-q3_K_L")

checkpointer = MemorySaver()

# === Resume Formatter ===
RESUME_BASE_URL = "https://test.com/resumes"

def format_resume(doc, i):
    file_name = doc.metadata.get("source", f"resume_{i+1}.pdf")
    resume_url = f"{RESUME_BASE_URL}/{file_name}"

    try:
        parsed = json.loads(doc.page_content)
    except:
        parsed = {"raw": doc.page_content}

    summary = [f"Candidate {i+1} - File: {file_name}"]
    fields = [
        "Name", "Email", "Phone", "Current Job Title", "Experience Years",
        "Skills", "Education", "Certifications", "Previous Job Titles",
        "Companies Worked At", "Projects", "Languages", "LinkedIn Profile", "Location"
    ]
    for field in fields:
        value = parsed.get(field)
        if value:
            summary.append(f"{field}: {value}")
    summary.append(f"Resume Link: {resume_url}")
    return "\n".join(summary)

# === Let LLM decide top-k ===
def extract_top_k(query: str) -> int:
    system = "Decide how many resumes (top-k) should be retrieved for this query. Respond ONLY with a number. E.g. '3'"
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": query}
    ]
    try:
        response = llm.invoke(messages)
        return int(response.content.strip())
    except:
        try:
            response = ollama_llm.invoke(messages)
        except Exception as fallback_error:
            print(f"Ollama also failed: {fallback_error}")
            return {"messages": [{"content": "All LLMs failed to respond."}]}

# === Main Routing Logic ===
def search_router(query: str, chat_mode: str, thread_id: str):
  
    k = extract_top_k(query)
    print(f"LLM decided top-{k} resumes to fetch.")

   
    if chat_mode == "A1":
        vectorstore = load_entity_vectorstore2()  
    else:
        vectorstore = load_entity_vectorstore()   

    if vectorstore is None:
        return "No vectorstore found for the selected mode."

    
    docs = vectorstore.similarity_search(query, k=k)
    if not docs:
        return "No matching resumes found."

    
    formatted_resumes = [
        f"[View Resume {i+1}: {doc.metadata.get('source')}]('?view={doc.metadata.get('source')}')"
    for i, doc in enumerate(docs)
    ]
    links_text = "\n\n".join(formatted_resumes)

    formatted_context = "\n\n".join(format_resume(doc, i) for i, doc in enumerate(docs))
    
    if chat_mode == "A1":
        tool_input = json.dumps({
            "question": query,
            "context": formatted_context
        })
        result = resume_chat_agent.invoke({"tool_input": tool_input})
        model_response = result["final_output"]

    else:
        
            messages = [{"role": "user", "content": query}]
            response = invoke_with_fallback(messages, thread_id)
            #safe_output = html.escape(response["messages"][-1].content)
            print("The actual response is: ", response)
            model_response= response["messages"][-1].content  #response["messages"][-1]["content"]
            print("The response from llm",model_response)
            # if "<function>" in model_response or "<\function>" in model_response:
            #     model_response= response["messages"][-1]["content"]
            # if "<function>" in model_response or "<\function>" in model_response:
            #     model_response= "Sorry not able to connect please try again after sometime"
           
        
    final_response = f"{model_response.strip()}" #\n\n\n### Resume Links:\n{links_text}
    return final_response

