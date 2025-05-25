import os
import io
import base64
import subprocess
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from typing import TypedDict, Optional, List
from paddleocr import PaddleOCR
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableLambda
from langchain.schema import Document
from vectorstore import load_vectorstore, create_vectorstore_from_docs
import requests
import streamlit as st
os.environ['GROQ_API_KEY'] = st.secrets["GROQ_API_KEY"]
# === Conversion Agent ===
class ConversionAgent:
    def __init__(self, soffice_path: str ='/usr/bin/soffice'):
        self.soffice_path = soffice_path

    def convert_to_pdf(self, input_path: str, output_dir: str = "converted") -> str:
        os.makedirs(output_dir, exist_ok=True)
        ext = os.path.splitext(input_path)[-1].lower()
        if ext == ".pdf":
            return input_path

        try:
            subprocess.run([
                self.soffice_path, "--headless", "--convert-to", "pdf", input_path, "--outdir", output_dir
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            base = os.path.splitext(os.path.basename(input_path))[0]
            return os.path.join(output_dir, f"{base}.pdf")
        except Exception as e:
            raise RuntimeError(f"Conversion failed for {input_path}: {e}")

# === OCR Handler ===
class OCRHandler:
    def __init__(self, groq_api_key: str):
        self.api_key = groq_api_key
        self.models = [
            "llama-3.2-90b-vision-preview",
            "llama-3.2-11b-vision-preview",
            "meta-llama/llama-4-scout-17b-16e-instruct"
        ]
        self.headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        self.paddle = PaddleOCR(use_angle_cls=True, lang='en',use_gpu=False)

    def ocr_image(self, image: Image.Image) -> str:
        for model in self.models:
            try:
                print(f" Trying Groq model: {model}")
                img_base64 = self._image_to_base64(image)
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}},
                                {"type": "text", "text": "Extract all text exactly as it appears, preserve line breaks."}
                            ]
                        }
                    ]
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=self.headers, json=payload)
                result = res.json()
                return result['choices'][0]['message']['content'].strip()
            except Exception as e:
                print(f" Groq {model} failed:", e)
                continue

        try:
            print(" Falling back to PaddleOCR...")
            result = self.paddle.ocr(np.array(image), cls=True)
            return "\n".join([line[1][0] for block in result for line in block])
        except Exception as e:
            print(f" PaddleOCR failed:", e)

        try:
            print(" Falling back to Ollama...")
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            encoded = base64.b64encode(img_bytes.getvalue()).decode()
            data = {"model": "llava", "prompt": "Extract all visible text.", "images": [encoded]}
            result = requests.post("http://localhost:11434/api/generate", json=data)
            return result.json().get("response", "").strip()
        except Exception as e:
            print(f" Ollama failed:", e)
            return "[OCR Failed]"

    def _image_to_base64(self, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

# === LangGraph State ===
class ResumeState(TypedDict):
    file_paths: List[str]
    converted_paths: List[str]
    extracted_texts: List[str]

# === Text Cleanup ===
def clean_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip() and not line.strip().lower().startswith("page")).strip()

# === OCR Processor ===
ocr_engine = OCRHandler(groq_api_key=st.secrets["GROQ_API_KEY"])

def process_resumes(state: ResumeState) -> ResumeState:
    file_paths = state["converted_paths"]
    extracted_texts1 = state.get("extracted_texts", [])

    vectorstore = load_vectorstore()
    already_indexed = []
    new_files = []

    if vectorstore:
        all_docs = vectorstore.docstore._dict.values() if hasattr(vectorstore.docstore, "_dict") else []
        for file_path in file_paths:
            matched_docs = [doc for doc in all_docs if doc.metadata.get("source") == file_path]
            if matched_docs:
                page_wise = [f"Page {i+1}:\n{doc.page_content}" for i, doc in enumerate(matched_docs)]
                extracted_texts1.append("\n\n".join(page_wise))
                already_indexed.append(file_path)
            else:
                new_files.append(file_path)
    else:
        new_files = file_paths

    extracted_docs = []

    for file_path in new_files:
        print(f" Processing: {file_path}")
        doc = fitz.open(file_path)
        all_text = []

        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            text = ocr_engine.ocr_image(img)
            all_text.append(text)

        full_text1 = "\n\n".join([f"Page {i+1}:\n{text}" for i, text in enumerate(all_text)])
        cleaned1 = clean_text(full_text1)
        extracted_texts1.append(cleaned1)
        extracted_docs.append(Document(page_content=cleaned1, metadata={"source": file_path}))

    if extracted_docs:
        if vectorstore is None:
            vectorstore = create_vectorstore_from_docs(extracted_docs)
        else:
            vectorstore.add_documents(extracted_docs)
            vectorstore.save_local("resume_index")
            print(f" Added {len(extracted_docs)} new documents.")

    return {"extracted_texts": extracted_texts1}

# === Conversion Node ===
def convert_to_pdf_node(state: ResumeState) -> ResumeState:
    converter = ConversionAgent()
    converted = []

    for path in state["file_paths"]:
        print(f"Converting {path} to PDF...")
        pdf_path = converter.convert_to_pdf(path)
        converted.append(pdf_path)

    return {"converted_paths": converted}

# === LangGraph Pipeline ===
builder = StateGraph(ResumeState)
builder.add_node("convert_files", RunnableLambda(convert_to_pdf_node))
builder.add_node("process_files", RunnableLambda(process_resumes))

builder.set_entry_point("convert_files")
builder.add_edge("convert_files", "process_files")
builder.set_finish_point("process_files")

graph = builder.compile()
memory = MemorySaver()
ocr_pipeline = graph.with_config({"checkpointer": memory})
