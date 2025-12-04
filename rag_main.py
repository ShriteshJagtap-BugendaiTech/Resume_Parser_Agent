from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_ollama import OllamaLLM
from vectorstore1 import load_entity_vectorstore
import json
from langchain_ollama import ChatOllama
import streamlit as st
import os
os.environ['GROQ_API_KEY'] = st.secrets["GROQ_API_KEY"]
# === Load the vectorstore ===
vectorstore = load_entity_vectorstore()

# === Define a tool from the vectorstore ===
@tool
def search_resume(query: str) -> str:
    """
    Search indexed resume entities and return top matching candidate summaries.
    """
    docs = vectorstore.similarity_search(query, k=3)

    if not docs:
        return "No relevant resumes found for your query."

    results = []
    for i, doc in enumerate(docs, start=1):
        file_name = doc.metadata.get("source", "Unknown")
        try:
            parsed = json.loads(doc.page_content)
        except json.JSONDecodeError:
            parsed = {"raw": doc.page_content}

        summary_lines = [f"Candidate {i} - File: {file_name}"]

        for field in ["Name", "Email", "Skills", "Experience", "Education"]:
            value = parsed.get(field)
            if value:
                summary_lines.append(f"{field}: {value}")

        results.append("\n".join(summary_lines))

    return "\n\n".join(results)


tools = [search_resume]

# === Setup memory checkpoint ===
checkpointer = MemorySaver()

# === Setup multiple LLMs ===
groq_api_key =st.secrets["GROQ_API_KEY"]

models = [
    ChatGroq(api_key=groq_api_key, model_name="meta-llama/llama-guard-4-12b"),
    ChatGroq(api_key=groq_api_key, model_name="llama-3.3-70b-versatile"),
    ChatGroq(api_key=groq_api_key, model_name="llama-3.1-8b-instant"),
    ChatGroq(api_key=groq_api_key, model_name="whisper-large-v3")
]

agent_prompt = """
You are an AI assistant for a recruitment system. Your task is to help users find suitable job candidates based on their queries. You do this by using a tool called `search_resume` that retrieves structured resume data.

Rules and Guidelines:

1. ONLY respond to questions related to resumes or candidate search. If the user asks anything unrelated (e.g., math, trivia, general questions), respond with:
   "I'm only able to help with resume-related queries. Please ask about candidate search or resume insights."

2. Use the `search_resume` tool to answer all resume-related questions. Do NOT generate candidate names, profiles, or summaries yourself.

3. A candidate is valid ONLY if their name appears in the structured data returned by the `search_resume` tool. If a name appears in hobbies, interests, or references, but not as a "Name" field in the parsed resume data, ignore it.

4. Do not invent or assume candidate names. Only summarize or present what is explicitly provided by the tool output.

5. Respect the number of results requested (e.g., top 5 candidates). If fewer valid results are available, say so clearly.

6. Format responses clearly and concisely.

7. Do not speculate. If a query is unclear or cannot be fulfilled with available data, say:
   "I couldn't find enough matching resumes for that query."

Stay factual, structured, and focused only on resume data.
"""

fallback_llm = ChatOllama(model="llama3.2:1b-instruct-q3_K_L")
#fallback_llm = ChatGroq(api_key=groq_api_key, model_name="llama3-8b-8192")

# Function to attempt multiple Groq models sequentially with tool handling
def invoke_with_fallback(messages, thread_id):
    for llm in models:
        try:
            app = create_react_agent(llm, tools, checkpointer=checkpointer,prompt = agent_prompt)
            response = app.invoke(
                {"messages": messages},
                config={"configurable": {"thread_id": thread_id}}
            )

            # Handle tool execution
            while response['messages'][-1].tool_calls:
                tool_call = response['messages'][-1].tool_calls[0]
                tool_name = tool_call['name']
                tool_args = json.loads(tool_call['args'])

                tool_output = search_resume(**tool_args)

                messages.append(response['messages'][-1])
                messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": tool_output,
                    "tool_call_id": tool_call['id']
                })

                response = app.invoke(
                    {"messages": messages},
                    config={"configurable": {"thread_id": thread_id}}
                )

            return response

        except Exception:
            continue

    fallback_app = create_react_agent(fallback_llm, tools, checkpointer=checkpointer,prompt = agent_prompt)

    response = fallback_app.invoke(
        {"messages": messages},
        config={"configurable": {"thread_id": thread_id}}
    )

    while response['messages'][-1].tool_calls:
        tool_call = response['messages'][-1].tool_calls[0]
        tool_name = tool_call['name']
        tool_args = json.loads(tool_call['args'])

        tool_output = search_resume(**tool_args)

        messages.append(response['messages'][-1])
        messages.append({
            "role": "tool",
            "name": tool_name,
            "content": tool_output,
            "tool_call_id": tool_call['id']
        })

        response = fallback_app.invoke(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id}}
        )

    return response

thread_id = 42

