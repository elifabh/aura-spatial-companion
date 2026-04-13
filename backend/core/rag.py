"""
RAG Module — ChromaDB knowledge retrieval.
Stores and queries Irish health & demographic knowledge
for contextual recommendations.
"""

import chromadb
from backend.config import CHROMA_PERSIST_DIR

# Initialise persistent ChromaDB client
_client: chromadb.ClientAPI | None = None
COLLECTION_NAME = "aura_knowledge"


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create the ChromaDB persistent client."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _client


def get_collection():
    """Get or create the main knowledge collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Irish health and demographic knowledge base"},
    )


def add_knowledge(text: str, metadata: dict | None = None, doc_id: str | None = None):
    """Add a knowledge document to the collection."""
    collection = get_collection()
    import uuid
    doc_id = doc_id or str(uuid.uuid4())
    collection.add(
        documents=[text],
        metadatas=[metadata or {}],
        ids=[doc_id],
    )
    return doc_id


def get_relevant_knowledge(
    query: str,
    profile: dict | None = None,
    n_results: int = 5,
) -> list[dict]:
    """
    Query the knowledge base for relevant context.
    Combines ChromaDB vector search with Graph RAG relationship chains.
    Profile-aware: enriches query with detected group keywords for better retrieval.
    Returns a list of dicts with 'text' and 'metadata' keys.
    """
    collection = get_collection()
    knowledge = []

    # Profile-aware query enrichment
    enriched_query = query
    if profile:
        try:
            from backend.core.group_rules import detect_groups
            groups = detect_groups(profile)
            group_keywords = {
                "child": "child safety toddler",
                "child_baby": "baby infant safety",
                "elderly": "elderly falls prevention accessibility",
                "disability_motor": "wheelchair mobility accessibility",
                "disability_visual": "visual impairment contrast lighting",
                "remote_worker": "ergonomic desk workspace",
                "student": "study concentration focus",
                "pregnant": "pregnancy safety ventilation",
                "wellness": "meditation calm relaxation",
                "fitness": "exercise space workout",
            }
            extras = [group_keywords.get(g, "") for g in groups if g in group_keywords]
            if extras:
                enriched_query = f"{query} {' '.join(extras)}"
        except Exception:
            pass

    # 1. ChromaDB vector search
    if collection.count() > 0:
        results = collection.query(
            query_texts=[enriched_query],
            n_results=min(n_results, collection.count()),
        )

        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                knowledge.append({"text": doc, "metadata": meta})

    # 2. Graph RAG relationship chains
    try:
        from backend.db.graph import get_graph_context
        graph_chains = get_graph_context(query)
        if graph_chains:
            graph_text = "Knowledge Graph Relationships:\n" + "\n".join(graph_chains)
            knowledge.append({
                "text": graph_text,
                "metadata": {"source": "knowledge_graph", "category": "graph_rag"}
            })
    except Exception as e:
        print(f"[RAG] Graph context error: {e}")

    return knowledge


def seed_knowledge_base():
    """Seed the knowledge base with initial Irish health & safety data."""
    initial_docs = [
        {
            "text": (
                "In Ireland, the Health Service Executive (HSE) recommends that "
                "homes with young children should secure heavy furniture to walls, "
                "use safety gates on stairs, and keep small objects out of reach. "
                "Window blinds should have breakaway cords."
            ),
            "metadata": {"category": "safety", "demographic": "children"},
        },
        {
            "text": (
                "For elderly residents in Ireland, Age Action recommends removing "
                "loose rugs, ensuring adequate lighting on stairs and hallways, "
                "installing grab rails in bathrooms, and keeping frequently used "
                "items at accessible heights."
            ),
            "metadata": {"category": "safety", "demographic": "elderly"},
        },
        {
            "text": (
                "Irish homes often have limited natural light due to cloud cover. "
                "Maximising light through mirror placement, light-coloured walls, "
                "and keeping windows clear can significantly improve wellbeing. "
                "SAD (Seasonal Affective Disorder) affects up to 12% of the Irish population."
            ),
            "metadata": {"category": "lighting", "demographic": "general"},
        },
        {
            "text": (
                "Indoor air quality in Irish homes can be improved by regular "
                "ventilation, especially in rooms with gas appliances. The SEAI "
                "recommends opening windows for at least 15 minutes daily. "
                "Houseplants like spider plants and peace lilies can help filter air."
            ),
            "metadata": {"category": "air_quality", "demographic": "general"},
        },
        {
            "text": (
                "Montessori-inspired home environments for toddlers (12-36 months) "
                "include low shelves with rotating toy selections, child-height "
                "artwork, a floor bed or low mattress, and designated activity zones. "
                "These support independence and reduce hyperactive behaviour."
            ),
            "metadata": {"category": "activity", "demographic": "preschool"},
        },
    ]

    for doc in initial_docs:
        add_knowledge(text=doc["text"], metadata=doc["metadata"])

    print(f"[Aura] Seeded knowledge base with {len(initial_docs)} documents.")
