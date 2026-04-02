"""
Vision Module — Spatial image analysis via LLaVA.
Processes camera images to understand the user's living space.
"""

import httpx
from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL

VISION_PROMPT = """Analyse this image of a living space. Provide:
1. A brief description of the space
2. A list of objects/furniture you can identify
3. Practical suggestions to improve the space WITHOUT purchases

Focus on:
- Safety (especially for children and elderly)
- Natural light and ventilation
- Organisation and flow
- Comfort and accessibility

Format your response as JSON with keys:
- description (string)
- objects_detected (list of strings)
- suggestions (list of strings)
"""


async def analyse_space_image(
    image_b64: str,
    user_id: str = "default",
) -> dict:
    """
    Send an image to LLaVA for spatial analysis.
    Returns a dict with description, objects_detected, suggestions.
    """
    request_body = {
        "model": OLLAMA_MODEL,
        "prompt": VISION_PROMPT,
        "images": [image_b64],
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

    import json
    try:
        result = json.loads(data.get("response", "{}"))
        return {
            "description": result.get("description", ""),
            "objects_detected": result.get("objects_detected", []),
            "suggestions": result.get("suggestions", []),
        }
    except json.JSONDecodeError:
        return {
            "description": data.get("response", "Unable to analyse image."),
            "objects_detected": [],
            "suggestions": [],
        }
