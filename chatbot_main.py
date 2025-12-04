from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda
import json
from typing import TypedDict, Optional
import streamlit as st
import os
os.environ['GROQ_API_KEY'] = st.secrets["GROQ_API_KEY"]
# === Tool ===
@tool
def resume_qa_tool(input: str) -> str:
    """Answers questions based on resume context. Input must be a JSON string with 'question' and 'context' keys."""
    data = json.loads(input)
    question = data["question"]
    context = data["context"]

    prompt = f"""
You are an AI assistant that answers questions about resumes.

Here are the combined resumes:
\"\"\"{context}\"\"\"

Answer this question based only on the resumes above:
\"{question}\"
if the user asks a question that is not related to resumes, kindly decline request.Do not answer if questions are not realated to resumes.If user ask question in informal way or disrespective way then do not answer the question.
"""
    try:
        print("→ Using Groq...")
        llm = ChatOpenAI(
            model="llama-3.3-70b-versatile",
            base_url="https://api.groq.com/openai/v1",
            api_key=st.secrets["GROQ_API_KEY"],
            temperature=0.2,
        )
        return llm.invoke(prompt).content
    except Exception as e:
        print(f"Groq failed: {e}")
        print("Falling back to Ollama...")
        try:
            fallback_llm = ChatOllama(model="llama3.2:latest", temperature=0.2)
            return fallback_llm.invoke(prompt).content
        except Exception as e2:
            return f"Both Groq and Ollama failed: {e2}"


# === Define the agent's state ===
class AgentState(TypedDict):
    tool_input: Optional[str]
    final_output: Optional[str]

# === Node logic ===
def run_resume_tool(state: AgentState) -> AgentState:
    result = resume_qa_tool.invoke(state["tool_input"])
    return {"final_output": result}


# === Build LangGraph ===
builder = StateGraph(AgentState)
builder.add_node("qa_tool", RunnableLambda(run_resume_tool))
builder.set_entry_point("qa_tool")
builder.set_finish_point("qa_tool")
graph = builder.compile()

# === Add memory ===
memory = MemorySaver()
app = graph.with_config({"checkpointer": memory})
resume_chat_agent = app


