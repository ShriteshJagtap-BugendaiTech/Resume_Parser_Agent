import os
import re
import json
from typing import List, Dict, Union, TypedDict
from pathlib import Path
import shutil
from ocr_main import ocr_pipeline
from entity_main import resume_extraction_agent
from chatbot_main import resume_chat_agent
from vectorstore1 import create_entity_vectorstore, load_entity_vectorstore
from vectorstore2 import create_entity_vectorstore2, load_entity_vectorstore2
from rag_main import invoke_with_fallback, thread_id
import streamlit as st
from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from search3 import search_router



ENTITY_VECTORSTORE_DIR_A1 = "resume_entities_chatbot"

def extract_clean_json(text: str) -> str:
    # === Case 1: JSON inside a code block (```json ... ```)
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if code_block_match:
        return code_block_match.group(1).strip()

    # === Case 2: JSON follows a known preamble like "Here is the parsed..."
    preamble_match = re.search(r"(Here is.*?JSON format:)?\s*\{[\s\S]*", text)
    if preamble_match:
        json_start = preamble_match.group(0).strip()
        # Try to trim to a well-formed JSON object by balancing braces
        open_braces = 0
        for i, c in enumerate(json_start):
            if c == '{':
                open_braces += 1
            elif c == '}':
                open_braces -= 1
            if open_braces == 0:
                return json_start[:i+1]  # Return up to the matching closing brace

    # === Case 3: Grab first {...} block (non-greedy)
    brace_block = re.search(r"(\{.*?\})", text, re.DOTALL)
    if brace_block:
        return brace_block.group(1).strip()

    # === Fallback: Return entire text
    return text.strip()




# === LangGraph State ===
class SupervisorState(TypedDict):
    file_paths: List[str]
    extracted_texts: List[str]
    entities: List[Dict]
    answer: str
    query: str
    chat_mode: str  
    ocr_retries: int

# === Node 1: OCR (uses tested working pipeline)
def ocr_node(state: SupervisorState) -> SupervisorState:
    print("[OCR Node] Input files:", state["file_paths"])
    input_payload = {"file_paths": state["file_paths"]}
    result = {}
    for step in ocr_pipeline.stream(input_payload):
        result.update(step)
    extracted = result.get("extracted_texts", [])
    print("[OCR Node] Extracted:", len(extracted))
    return {"extracted_texts": extracted}


def entity_extraction_node(state: SupervisorState) -> SupervisorState:
    print("[Entity Node] Starting extraction...")
    file_paths = [Path(p) for p in state["file_paths"]]
    texts = state["extracted_texts"]
    chat_mode = state["chat_mode"]
    vectorstore=None
    if chat_mode=="A1":
        vectorstore = load_entity_vectorstore2()
    else:
        vectorstore = load_entity_vectorstore()
    
    print("The chat mode: ",chat_mode)
    
    
    
    all_entities = []
    new_entities = []
    MAX_RETRIES = 5 

    for file, text in zip(file_paths, texts):
        filename = file.name
        existing_entity = None

        if vectorstore:
            for doc in vectorstore.docstore._dict.values():
                if doc.metadata.get("source") == filename:
                    try:
                        existing_entity = json.loads(doc.page_content)
                        print(f"[Entity Node] Found cached entity for: {filename}")
                        all_entities.append({"file": filename, "entities": existing_entity})
                        break
                    except json.JSONDecodeError:
                        pass

        # Only run extraction if not cached
        if not existing_entity:
            parsed = None
            for attempt in range(MAX_RETRIES):
                print(f"[Entity Node] Extracting new entity for: {filename}, Attempt: {attempt+1}")
                result = {}
                for step in resume_extraction_agent.stream({"tool_input": text}):
                    result.update(step)

                raw_output = result.get("extract_entities", {}).get("final_output") or result.get("final_output", "")
                json_str = extract_clean_json(raw_output)

                try:
                    parsed = json.loads(json_str)
                    if not parsed or "error" in parsed:
                        print(f"[Entity Node] Invalid JSON content, will retry.")
                        parsed = None
                    elif not parsed.get("Email"):
                        print("[Entity Node] Missing 'name' or 'email', will retry.")
                        parsed = None
                    else:
                        break  # Valid parse
                except json.JSONDecodeError:
                    print(f"[Entity Node] JSON decode error, will retry.")
                    parsed = None
                    
            if not parsed or parsed == None:
                st.error("There was an issue parsing the resume data. Please re-upload a clearer file.")
                st.stop()
            if parsed:
                parsed["File"] = filename
                all_entities.append({"file": filename, "entities": parsed})
                new_entities.append({"file": filename, "entities": parsed})
            else:
                print(f"[Entity Node] Failed to extract valid entity for: {filename} after {MAX_RETRIES} attempts.")
    if new_entities and chat_mode == "A2":
        create_entity_vectorstore(new_entities)
    if new_entities and chat_mode == "A1":
        print("For chatbot part")
        if os.path.exists(ENTITY_VECTORSTORE_DIR_A1):
            print("[Entity Node] Removing old A1 vectorstore...")
            shutil.rmtree(ENTITY_VECTORSTORE_DIR_A1)
        create_entity_vectorstore2(new_entities)
    #print("Entities", all_entities)

    print("[Entity Node] Total extracted entities:", len(all_entities))
    return {"entities": all_entities}

# === Node 3: QA Step
def qa_node(state: SupervisorState) -> SupervisorState:
    print("[QA Node] Running QA for query:", state["query"])
    files = [Path(p) for p in state["file_paths"]]
    texts = state["extracted_texts"]
    query = state["query"]
    chat_mode = state["chat_mode"]
    thread = "session-1001"
    answer = "[Chatbot failed]"
    #print("[QA Node] Chat mode:", chat_mode)
    try:
        response = search_router(query, chat_mode, thread)
        answer = response
       
    except Exception as e:
        answer = f"[QA Error: {str(e)}]"

    #print("[QA Node] Answer:", answer[:100] + "..." if len(answer) > 100 else answer)
    return {"answer": answer}

def supervisor_router(state: SupervisorState) -> Union[str, List[str]]:
    
    if not state.get("extracted_texts"):
        retries = state.get("ocr_retries", 0)
        if retries < MAX_OCR_RETRIES:
            print("[Supervisor] No text; retrying OCR...")
            # bump retry count for next run of ocr_step
            state["ocr_retries"] = retries + 1
            return "ocr_step"      # 👈 allowed now because mapping includes it
        else:
            msg = "OCR could not extract text from the uploaded files. Please check the PDFs or upload clearer files."
            print("[Supervisor]", msg)
            try:
                st.error(msg)
            except Exception:
                pass
            return END
    
    
    next_steps = []
    if not state.get("entities"):
        next_steps.append("entity_extraction_step")
    if state.get("query"):
        next_steps.append("qa_step")
    
    return next_steps or END

# === Build LangGraph
builder = StateGraph(SupervisorState)

builder.add_node("ocr_step", RunnableLambda(ocr_node))
builder.add_node("entity_extraction_step", RunnableLambda(entity_extraction_node))
builder.add_node("qa_step", RunnableLambda(qa_node))
builder.set_entry_point("ocr_step")
builder.add_conditional_edges("ocr_step", supervisor_router, {
    "entity_extraction_step": "entity_extraction_step",
    "qa_step": "qa_step",
    END: END
})

builder.add_edge("entity_extraction_step", END)
builder.add_edge("qa_step", END)

compiled_graph = builder.compile()
memory = MemorySaver()
pipeline = compiled_graph.with_config({"checkpointer": memory})
MAX_OCR_RETRIES = 2
# === Wrapper Class
class SupervisorAgent:
    def run(self, files: List[Union[str, Path]], query: str, chat_mode: str) -> Dict:
        file_paths = [str(f) for f in files]
        initial_state: SupervisorState = {
            "file_paths": file_paths,
            "extracted_texts": [],
            "entities": [],
            "answer": "",
            "query": query,
            "chat_mode": chat_mode,
            "ocr_retries": 0,
        }

        final_state = {
        "file_paths": file_paths,
        "extracted_texts": [],
        "entities": [],
        "answer": "",
        "query": query,
        "chat_mode": chat_mode
    }
        for step in pipeline.stream(initial_state):
            for key, val in step.items():
                if key in ["ocr_step", "entity_extraction_step", "qa_step"]:
                    final_state.update(val)  # these contain nested state updates
                else:
                    final_state[key] = val

        #print("[Final Merged State Keys]:", list(final_state.keys()))
        return {
            "entities": final_state.get("entities", []),
            "answer": final_state.get("answer", "[Pipeline failed]"),
            "extracted_texts": final_state.get("extracted_texts", [])
        }
