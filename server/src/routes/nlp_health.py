"""
server/src/routes/nlp_health.py
"""

from fastapi import APIRouter
from pydantic import BaseModel
import os
from pathlib import Path

router = APIRouter(prefix="/api/nlp", tags=["NLP Health"])

class NLPHealthStatus(BaseModel):
    llm: bool
    embeddings: bool
    knowledge_base: bool
    retrieval: bool
    status: str

@router.get("/health", response_model=NLPHealthStatus)
def nlp_health_check():
    # Check LLM config
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    has_llm = bool(api_key)

    # Check Embeddings
    has_embeddings = False
    try:
        __import__("sentence_transformers")
        has_embeddings = True
    except ImportError:
        pass

    # Check Knowledge base
    kb_paths = [
        Path("data/knowledge"),
        Path("nlp/data/knowledge"),
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "knowledge",
        Path(__file__).resolve().parent.parent.parent.parent / "nlp" / "data" / "knowledge"
    ]
    
    has_kb = any(p.exists() and p.is_dir() for p in kb_paths)
    
    status = "healthy" if has_llm and has_embeddings and has_kb else "degraded"
    if not has_llm and not has_kb:
        status = "critical"

    return NLPHealthStatus(
        llm=has_llm,
        embeddings=has_embeddings,
        knowledge_base=has_kb,
        retrieval=has_kb,
        status=status
    )
