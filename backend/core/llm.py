"""
LLM Integration — Ollama + LLaVA (local inference).
Handles all natural language generation for Aura.
Zero cloud dependency.
"""

import httpx
from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL

SYSTEM_PROMPT = """You are Aura, a warm and knowledgeable spatial companion.
Your philosophy is: "Live better with what you have."

Guidelines:
- Never suggest purchases or major renovations
- Focus on rearranging, repurposing, and small changes
- Be mindful of safety for children, elderly, and mobility-impaired users
- Consider Irish weather, culture, and living conditions
- Be empathetic, practical, and encouraging
- Keep responses concise but helpful
"""


async def generate_response(
    user_message: str,
    user_id: str = "default",
    image_b64: str | None = None,
) -> tuple[str, list[str]]:
    """
    Generate a conversational response using Ollama.
    Returns (reply_text, context_sources_used).
    """
    # Build the RAG context
    from backend.core.rag import get_relevant_knowledge
    from backend.services.profile import get_user_profile

    profile = get_user_profile(user_id)
    knowledge_chunks = get_relevant_knowledge(user_message, profile)
    context_texts = [chunk["text"] for chunk in knowledge_chunks] if knowledge_chunks else []

    # Compose the prompt
    context_block = "\n".join(context_texts) if context_texts else "No additional context."
    full_prompt = (
        f"[Context from knowledge base]\n{context_block}\n\n"
        f"[User message]\n{user_message}"
    )

    # Build the Ollama request
    request_body = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
    }
    if image_b64:
        request_body["images"] = [image_b64]

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=request_body,
        )
        response.raise_for_status()
        data = response.json()

    return data.get("response", ""), context_texts


async def generate_recommendation(
    profile: dict,
    knowledge: list[dict],
    context: str = "",
) -> list[dict]:
    """
    Generate personalised recommendations using the LLM.
    Returns a list of recommendation dicts.
    """
    knowledge_text = "\n".join(
        [k.get("text", "") for k in knowledge]
    ) if knowledge else "No additional knowledge."

    profile_summary = (
        f"Household: {profile.get('household_members', 'unknown')}\n"
        f"Mobility: {profile.get('mobility_notes', 'none noted')}\n"
        f"Interests: {profile.get('interests', 'general')}\n"
        f"Space type: {profile.get('space_type', 'unknown')}"
    ) if profile else "No profile available."

    prompt = (
        f"Based on this user profile:\n{profile_summary}\n\n"
        f"And this knowledge:\n{knowledge_text}\n\n"
        f"Current context: {context}\n\n"
        "Generate 3 personalised spatial recommendations. "
        "Remember: no purchases, no major changes. "
        "Format each as JSON with keys: title, description, category, relevance_score."
    )

    request_body = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=request_body,
        )
        response.raise_for_status()
        data = response.json()

    # Parse LLM JSON output
    import json
    try:
        result = json.loads(data.get("response", "[]"))
        if isinstance(result, dict) and "recommendations" in result:
            return result["recommendations"]
        if isinstance(result, list):
            return result
        return [result]
    except json.JSONDecodeError:
        return [{
            "title": "General tip",
            "description": data.get("response", "No recommendation available."),
            "category": "comfort",
            "relevance_score": 0.5,
        }]
