from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda
import json
from datetime import date
from typing import TypedDict, Optional
from ast import literal_eval
from datetime import date
import traceback
import streamlit as st
import os
os.environ['GROQ_API_KEY'] = st.secrets["GROQ_API_KEY"]
# === Tool ===
@tool
def resume_entity_extractor(input: str) -> str:
    """Extracts structured information from a resume. Input must be a raw resume string."""
    current_year = date.today().year
    print("[resume_entity_extractor] Current year:", current_year)
    prompt = f"""
You are a highly accurate resume parsing agent. Your task is to extract key structured information from the given resume text.

Extract and return the following fields in **valid JSON format only** (no extra commentary or explanation):
- File: (name of the resume file, e.g., "john_doe_resume.pdf")
- Name: (full name of the candidate)
- Email: (primary email address)
- Phone: (primary phone number)
- Skills: (list of distinct skills mentioned, e.g., ["Python", "Project Management", "SQL"])
- Experience Years: (calculated as the current year {current_year} minus the earliest year mentioned in the resume)
- Education: (list of degrees with institutions, e.g., [{{"degree": "B.Sc. Computer Science", "institution": "XYZ University"}}])
- Certifications: (list of certifications if mentioned)
- Current Job Title: (most recent job title)
- Previous Job Titles: (list of earlier job titles, if available)
- Companies Worked At: (list of companies the candidate has worked at)
- Projects: (list of named or described projects, if available)
- Languages: (list of spoken or programming languages)
- LinkedIn Profile: (if a LinkedIn URL is present)
- Location: (city and/or country if provided)

Today's year is: {current_year}

Here is the resume text to parse:
\"\"\"{input}\"\"\"
"""

    #print("[resume_entity_extractor] Prompt:", prompt)
    try:
        #print("[resume_entity_extractor] Trying Groq...")
        llm = ChatOpenAI(
            model="llama3-70b-8192",
            base_url="https://api.groq.com/openai/v1",
            api_key=st.secrets["GROQ_API_KEY"],
            temperature=0.2,
        )
        #print("[resume_entity_extractor] Sending prompt to Groq...")
        response = llm.invoke(prompt)
        #print("[resume_entity_extractor] Groq responded.")
        return response.content
    except Exception as e:
        print(f"Groq failed: {e}")
        print("Falling back to Ollama...")
        try:
            fallback_llm = ChatOllama(model="llama3.2:latest", temperature=0.2)
            return fallback_llm.invoke(prompt).content
        except Exception as e2:
            return f"Both Groq and Ollama failed: {e2}"



class AgentState(TypedDict, total=False):
    tool_input: Optional[str]
    final_output: Optional[str]
    thinking: Optional[str]
    action: Optional[str]
    response: Optional[str]



def run_extraction_tool(state: AgentState) -> AgentState:
    #print("[DEBUG] Running extraction tool with input length:", len(state["tool_input"]))
    
    thinking = "Reading the resume text and extracting relevant fields using the resume_entity_extractor tool."
    action = "resume_entity_extractor"
    
    try:
        result = resume_entity_extractor.invoke(state["tool_input"])

        response = result
        #print("[DEBUG] Extraction result received.")
        #print("The response from llm is", response)
    except Exception as e:
        response = f"Error: {str(e)}"
        #print("[ERROR] Extraction tool failed:", response)

    return {
        "tool_input": state["tool_input"],
        "final_output": response,
        "thinking": thinking,
        "action": action,
        "response": response
    }


# === Build LangGraph ===
builder = StateGraph(AgentState)
builder.add_node("extract_entities", RunnableLambda(run_extraction_tool))
builder.set_entry_point("extract_entities")
builder.set_finish_point("extract_entities")
graph = builder.compile()

# === Add Memory ===
memory = MemorySaver()
app = graph.with_config({"checkpointer": memory})
resume_extraction_agent = app
import re
def extract_clean_json(text):
    # Try to extract JSON code block using regex
    match = re.search(r"```(?:json)?\s*({.*?})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    # Fallback: Try to extract plain JSON without backticks
    match = re.search(r"({.*})", text, re.DOTALL)
    if match:
        return match.group(1)
    return None

