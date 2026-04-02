"""
ChromaDB Connection — Managed through backend.core.rag module.
This file re-exports the RAG utilities for convenience.
"""

from backend.core.rag import (
    get_chroma_client,
    get_collection,
    add_knowledge,
    get_relevant_knowledge,
    seed_knowledge_base,
)

__all__ = [
    "get_chroma_client",
    "get_collection",
    "add_knowledge",
    "get_relevant_knowledge",
    "seed_knowledge_base",
]
