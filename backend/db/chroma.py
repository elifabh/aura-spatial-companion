"""
Vector Database — Local embeddings storage for Aura's multimodal memory.
Requires `chromadb`.
"""

import chromadb
from chromadb.config import Settings
from backend.config import CHROMA_PERSIST_DIR
from pathlib import Path
from datetime import datetime

_chroma_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        Path(CHROMA_PERSIST_DIR).parent.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    return _chroma_client

def get_room_scans_collection():
    client = get_chroma_client()
    return client.get_or_create_collection("room_scans")

def save_scan_embedding(user_id: str, description: str):
    """Saves a textual representation of a room into ChromaDB."""
    collection = get_room_scans_collection()
    doc_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    collection.add(
        documents=[description],
        metadatas=[{"user_id": user_id, "timestamp": datetime.now().isoformat()}],
        ids=[doc_id]
    )

def get_previous_scan(user_id: str, current_description: str) -> str:
    """Retrieves the most semantically similar previous scan for context, or just the most recent."""
    collection = get_room_scans_collection()
    
    try:
        results = collection.query(
            query_texts=[current_description],
            where={"user_id": user_id},
            n_results=1
        )
        
        if results['documents'] and len(results['documents'][0]) > 0:
            return results['documents'][0][0]
        return None
    except Exception as e:
        print(f"[ChromaDB] Error fetching previous scan: {e}")
        return None
