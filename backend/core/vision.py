"""
Vision Module — Spatial image analysis via LLaVA.
Processes camera images to understand the user's living space.
"""

import httpx
from backend.config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    OLLAMA_OPTIONS, OLLAMA_KEEP_ALIVE, OLLAMA_NUM_CTX,
)

def build_vision_prompt(profile_text: str = "", previous_context: str = None) -> str:
    base = f"""Analyse this image of a living space like a specialist spatial analyst. First, read the profile:
[USER PROFILE CONTEXT]
{profile_text}

You MUST follow these 4 chain-of-thought steps strictly:
Step 1: What do I see? (List objects, layout, light sources)
Step 2: Who lives here? (Match what you see against the user profile context)
Step 3: What are the risks? (Identify safety, comfort, and accessibility hazards)
Step 4: What can be improved with NO purchases? (Provide specific, actionable, ranked suggestions)

Format your response EXACTLY as a JSON object with these keys:
- "description": (string) Summary of your Step 1 and Step 2 analysis.
- "objects_detected": (list of strings) Sourced from Step 1.
- "risks_identified": (list of strings) Sourced from Step 3.
- "suggestions": (list of objects) Sourced from Step 4. Each object must have:
    - "action": (string) The specific no-cost improvement.
    - "confidence": (integer 0-100) Your confidence that this will work.
    - "why_this_matters": (string) Personalised reasoning based strictly on the user profile.
- "score": (object) Integer keys: overall, light, air, safety, comfort (0-100).
- "comparison": (string) If previous context is provided, state what has changed.
"""
    if previous_context:
        base += f"\n[PREVIOUS SCAN CONTEXT]\n{previous_context}\n"
    return base

async def analyse_space_image(
    image_b64: str,
    user_id: str = "default",
) -> dict:
    from backend.db.chroma import get_previous_scan, save_scan_embedding
    from backend.services.profile import get_user_profile
    
    # 1. Get multimodal memory of the room
    previous_scan = get_previous_scan(user_id, "A living space")
    
    # 2. Get user profile
    profile = get_user_profile(user_id)
    profile_text = (
        f"Age: {profile.get('age', 'Unknown')}, "
        f"Mobility: {profile.get('mobility_notes', 'None')}, "
        f"Household: {profile.get('household_members', [])}, "
        f"Accessibility needs: {profile.get('accessibility_needs', [])}, "
        f"Concerns: {profile.get('concerns', 'None')}"
    ) if profile else "No known profile."

    prompt = build_vision_prompt(profile_text, previous_scan)

    request_body = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "images": [image_b64],
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

    import json
    
    # Defaults
    desc = ""
    objects = []
    risks = []
    suggestions = []
    score = {"overall": 0, "light": 0, "air": 0, "safety": 0, "comfort": 0}
    comparison = ""

    try:
        result = json.loads(data.get("response", "{}"))
        desc = result.get("description", "")
        objects = result.get("objects_detected", [])
        risks = result.get("risks_identified", [])
        suggestions = result.get("suggestions", [])
        raw_score = result.get("score", {})
        if isinstance(raw_score, dict):
            score["overall"] = int(raw_score.get("overall", 50))
            score["light"] = int(raw_score.get("light", 50))
            score["air"] = int(raw_score.get("air", 50))
            score["safety"] = int(raw_score.get("safety", 50))
            score["comfort"] = int(raw_score.get("comfort", 50))
        comparison = result.get("comparison", "")
    except Exception:
        # Fallback if json parsing fails
        desc = data.get("response", "")
        
    # Combine comparison if exists into description for DB
    full_desc = desc
    if comparison:
        full_desc += f"\n\nMemory Diff: {comparison}"

    # Save to Chroma DB for multimodal memory
    if desc.strip():
        save_scan_embedding(user_id, full_desc)

    return {
        "description": desc,
        "objects_detected": objects,
        "risks_identified": risks,
        "suggestions": suggestions,
        "score": score,
        "comparison": comparison
    }
