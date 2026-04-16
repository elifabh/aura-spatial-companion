"""
LLM Integration — Ollama + LLaVA (local inference).
Handles all natural language generation for Aura.
Zero cloud dependency.
"""

import httpx
import json
from backend.config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    OLLAMA_OPTIONS, OLLAMA_KEEP_ALIVE, OLLAMA_NUM_CTX,
)

from datetime import datetime


def validate_llm_response(text: str) -> str:
    """Post-validation guard: catch empty, nonsensical, or hallucinated LLM outputs."""
    if not text or not text.strip():
        return "I'm here to help with your space! Could you tell me more about what you'd like to improve?"
    # Remove common hallucination artifacts
    cleaned = text.strip()
    # If response is just repeated characters or very short nonsense
    if len(set(cleaned)) < 5 and len(cleaned) > 20:
        return "I'd love to help! Could you describe your space or ask me something specific?"
    return cleaned

SYSTEM_PROMPT = """You are Aura, a warm, caring spatial companion — like a thoughtful friend who knows a lot about home design, wellbeing, and safety.
Your philosophy is: "Live better with what you have."

How you speak:
- Talk like a kind, knowledgeable friend — NOT like a textbook or a report
- Use short, warm sentences. Be conversational, not clinical
- Say "you" and "your" — make it personal
- Use gentle humour when appropriate
- Give 2-3 practical tips maximum, not long lists
- Start with empathy ("I totally get that!" / "That sounds tricky!"), then give advice
- Use 2-3 relevant emojis per response to feel friendly (💡🪴✨🌿🛋️🏠🌧️☀️💛), but don't overdo it
- Use real-life examples: "You could try moving the lamp closer to your reading chair"
- NEVER recite guidelines word-for-word. You KNOW the guidelines — speak from that knowledge naturally
- NEVER say "The guidelines state..." or "According to the WHO..." — just give the advice as your own
- Keep responses under 150 words unless the user asks for detail

Content rules:
- Never suggest purchases or major renovations
- Focus on rearranging, repurposing, and small changes
- Consider Irish weather, culture, and living conditions
- Be mindful of safety for children, elderly, and mobility-impaired users

[LIFESTYLE ADVISOR PROTOCOLS]
- You don't just organise furniture; you organise routines.
- If morning is mentioned, emphasize: "Drink your coffee by the east-facing window to catch the morning light."
- If evening is mentioned, emphasize: "Turn off overhead lights; use a small lamp and a cozy blanket."
- Bed direction: If you know the sun azimuth, suggest placing the bed where morning natural light acts as an alarm.
- Music & Atmosphere: Suggest pairing natural light with specific music genres (e.g. classical on rainy days, bright acoustic on sunny mornings).
"""

def get_dynamic_system_prompt(profile: dict = None, mood: str = None) -> str:
    prompt = SYSTEM_PROMPT
    
    # 1. Seasonal Intelligence (Irish Low-Light Season)
    current_month = datetime.now().month
    if current_month in [10, 11, 12, 1, 2, 3]:
        prompt += "\n[SEASONAL CONTEXT: Oct-Mar] It is the Irish low-light season. Proactively consider Seasonal Affective Disorder (SAD) risks and deeply emphasize light optimization and warmth.\n"
    
    # 2. Profile-aware group rules (15+ archetypes)
    from backend.core.group_rules import build_group_prompt
    prompt += "\n" + build_group_prompt(profile) + "\n"
    
    # 3. Mood-adaptive conversation style
    if mood:
        from backend.core.mood_activities import get_mood_conversation_style
        prompt += "\n" + get_mood_conversation_style(mood, profile) + "\n"

    # 4. Safety boundaries
    from backend.core.safety import get_safety_system_prompt
    prompt += get_safety_system_prompt()
            
    return prompt


async def generate_response(
    user_message: str,
    user_id: str = "default",
    image_b64: str | None = None,
) -> tuple[str, list[str]]:
    """
    Generate a conversational response using Ollama.
    Returns (reply_text, context_sources_used).
    """
    # Build the RAG & Graph Context
    from backend.core.rag import get_relevant_knowledge
    from backend.services.profile import get_user_profile
    
    try:
        from backend.db.graph import get_graph_context
        graph_chains = get_graph_context(user_message)
    except Exception:
        graph_chains = []

    profile = get_user_profile(user_id)
    knowledge_chunks = get_relevant_knowledge(user_message, profile)
    context_texts = [chunk["text"] for chunk in knowledge_chunks] if knowledge_chunks else []

    # Compose the prompt
    profile_text = (
        f"User Profile => Household: {profile.get('household_members', 'unknown')}, "
        f"Mobility: {profile.get('mobility_notes', 'none noted')}, "
        f"Space: {profile.get('space_type', 'unknown')}"
    ) if profile else "No profile data."
    
    context_block = "\n".join(context_texts[:3]) if context_texts else ""  # Limit to top 3 chunks
    graph_block = "\n".join(graph_chains) if graph_chains else ""
    
    # Build prompt with instructions to NOT recite context
    knowledge_note = ""
    if context_block or graph_block:
        knowledge_note = "[Background knowledge — DO NOT quote this directly, just let it inform your answer naturally]\n"
        if context_block:
            knowledge_note += f"Vector Data:\n{context_block}\n\n"
        if graph_block:
            knowledge_note += f"Graph Relations:\n{graph_block}\n\n"
    
    # Sensory enrichment: detect mood/stress/relaxation keywords and inject
    # a music + scent hint so Aura can weave them into the reply naturally.
    sensory_block = ""
    try:
        from backend.core.music import detect_mood_from_text, get_sensory_context
        detected_mood = detect_mood_from_text(user_message)
        if detected_mood:
            ctx = get_sensory_context(detected_mood)
            if ctx:
                sensory_block = f"\n{ctx}\n"
    except Exception:
        pass

    full_prompt = (
        f"{knowledge_note}"
        f"[About this person]\n{profile_text}\n\n"
        f"[Their question]\n{user_message}\n"
        f"{sensory_block}\n"
        f"Remember: respond like a warm friend, not a textbook. Keep it short and personal."
    )

    # Build the Ollama request
    request_body = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "system": get_dynamic_system_prompt(profile),
        "stream": False,
        "options": {**OLLAMA_OPTIONS, "num_ctx": OLLAMA_NUM_CTX},
        "keep_alive": OLLAMA_KEEP_ALIVE,
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

    reply = validate_llm_response(data.get("response", ""))
    return reply, context_texts


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
        "system": get_dynamic_system_prompt(profile),
        "stream": False,
        "format": "json",
        "options": {**OLLAMA_OPTIONS, "num_ctx": OLLAMA_NUM_CTX},
        "keep_alive": OLLAMA_KEEP_ALIVE,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=request_body,
        )
        response.raise_for_status()
        data = response.json()

    # Parse LLM JSON output
    try:
        result = json.loads(data.get("response", "[]"))
        if isinstance(result, dict) and "recommendations" in result:
            items = result["recommendations"]
        elif isinstance(result, list):
            items = result
        else:
            items = [result]
        # Normalise field names: LLM sometimes returns "focus"/"reasoning"
        # instead of the requested "category"/"relevance_score".
        normalised = []
        for item in items:
            raw_score = (
                item.get("relevance_score")
                or item.get("reasoning_score")
                or item.get("reasoning")
            )
            try:
                score = float(raw_score) if raw_score is not None else 0.5
            except (ValueError, TypeError):
                score = 0.5
            normalised.append({
                "title": item.get("title", "Tip"),
                "description": item.get("description", ""),
                "category": item.get("category") or item.get("focus") or "comfort",
                "relevance_score": score,
            })
        return normalised
    except json.JSONDecodeError:
        return [{
            "title": "General tip",
            "description": data.get("response", "No recommendation available."),
            "category": "comfort",
            "relevance_score": 0.5,
        }]
