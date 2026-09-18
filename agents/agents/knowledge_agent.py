"""
ORCA Knowledge Agent
Handles KNOWLEDGE_QUERY intent by retrieving RAG content.
"""

from __future__ import annotations
import logging
from typing import Optional, Any

from nlp.rag.rag_pipeline import get_relevant_context
from nlp.orca_service import extract_evidence
from agents.orchestrator.state import AgentState

logger = logging.getLogger("neermitra.agents.knowledge")

def knowledge_agent(query: str) -> dict:
    """
    Run the ORCA Knowledge Agent.
    Retrieves facts and context for general marine knowledge questions.
    """
    try:
        context = get_relevant_context(query)
        evidence = extract_evidence(context)
        
        # Extract clean factual snippets (no metadata headers)
        facts = []
        if isinstance(context, dict):
            docs = context.get("documents", [])
            for doc in docs:
                if isinstance(doc, dict) and doc.get("text"):
                    facts.append(doc["text"].strip())
            if not facts and context.get("context"):
                facts.append(context["context"].strip())
        elif isinstance(context, list):
            for item in context:
                if isinstance(item, dict) and item.get("text"):
                    facts.append(item["text"].strip())
                elif isinstance(item, str):
                    facts.append(item.strip())
        elif isinstance(context, str) and context.strip():
            facts.append(context.strip())
            
        return {
            "facts": facts,
            "evidence": evidence
        }
    except Exception as e:
        logger.error(f"Knowledge agent failed: {e}")
        return {
            "facts": [],
            "evidence": {"sources": [], "chunks": []}
        }
