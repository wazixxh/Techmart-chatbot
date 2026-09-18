from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import sys
import json
import asyncio
from pathlib import Path

# Ensure the api directory is in sys.path so local imports work in Vercel Serverless
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

def sync_env_keys():
    found_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY")
        or os.environ.get("GEMINI_KEY")
        or os.environ.get("GOOGLE_KEY")
    )
    if found_key:
        os.environ["GEMINI_API_KEY"] = found_key
        os.environ["GOOGLE_API_KEY"] = found_key
        os.environ["GOOGLE_GENERATIVE_AI_API_KEY"] = found_key
    return found_key

sync_env_keys()

import rag
from langchain_core.messages import HumanMessage, AIMessage

app = FastAPI(title="TechMart Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy initialization of RAG engine to prevent import-time cold start timeouts
_engine = None

def get_engine():
    global _engine
    sync_env_keys()
    if _engine is None:
        _engine = rag.build_engine()
    return _engine

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

@app.get("/")
@app.get("/api")
@app.get("/api/health")
async def health_check():
    key = sync_env_keys()
    key_names_present = [
        k for k in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY"]
        if k in os.environ
    ]
    return {
        "status": "healthy",
        "service": "TechMart RAG Assistant",
        "api_key_configured": bool(key),
        "detected_key_names": key_names_present,
    }

@app.post("/api/chat")
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    messages = request.messages
    if not messages:
        return JSONResponse(status_code=400, content={"error": "No messages provided"})

    # Extract the latest question
    latest_msg = messages[-1]
    if latest_msg.get("role") != "user":
        return JSONResponse(status_code=400, content={"error": "Last message must be from user"})
    
    question = latest_msg.get("content", "")
    
    # Reconstruct history for LangChain
    history = []
    for m in messages[:-1]:
        if m.get("role") == "user":
            history.append(HumanMessage(content=m.get("content", "")))
        elif m.get("role") == "assistant":
            history.append(AIMessage(content=m.get("content", "")))

    async def generate():
        try:
            engine = get_engine()
            stream = engine.stream(question, history)
            
            # The first event may contain retrieval context (documents)
            first_event = next(stream, None)
            
            # Stream the answer chunks in Vercel AI SDK data protocol
            # Protocol: 0:"<text>"\n
            for event in stream:
                if "token" in event:
                    yield event["token"]
                elif "answer" in event:
                    answer_text = event["answer"]
                    words = answer_text.split(" ")
                    for i, word in enumerate(words):
                        chunk = word + (" " if i < len(words) - 1 else "")
                        yield chunk
                        await asyncio.sleep(0.015)
        except Exception as e:
            yield f"\n\n[Error: {str(e)}]"

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8",
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="0.0.0.0", port=8000, reload=True)
