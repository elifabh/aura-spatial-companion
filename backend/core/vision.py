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


# ─────────────────────────────────────────────────────────
# ZONE ANALYSIS
# ─────────────────────────────────────────────────────────

def build_zone_prompt(profile_text: str, groups: list) -> str:
    """Build an archetype-personalised prompt for spatial zone detection."""
    focus_parts = []
    if any(g in groups for g in ["child_baby", "child_toddler", "child"]):
        focus_parts.append("child safety (sharp corners, choking hazards, fall zones, exposed outlets)")
    if "elderly" in groups:
        focus_parts.append("fall prevention, clear pathways, furniture stability, night lighting")
    if "disability_motor" in groups:
        focus_parts.append("wheelchair clearance (min 90 cm), reach zones, stable surfaces")
    if "disability_visual" in groups:
        focus_parts.append("contrast zones, glare sources, texture differentiation areas")
    if "disability_hearing" in groups:
        focus_parts.append("visual alert zones, sightline clearance, reflective surfaces")
    if "remote_worker" in groups or "student" in groups:
        focus_parts.append("ergonomic work setup, screen glare, cable hazards")
    if "wellness" in groups or "fitness" in groups:
        focus_parts.append("movement space, ventilation quality, floor clearance")
    if not focus_parts:
        focus_parts.append("general safety, lighting quality, air circulation, comfort")

    focus_text = "\n".join(f"- {f}" for f in focus_parts)

    return f"""Analyse this image of a living space and identify 3 to 6 distinct spatial zones.

USER PROFILE:
{profile_text}

PRIORITY FOCUS AREAS FOR THIS PROFILE:
{focus_text}

Return a JSON object with EXACTLY this structure:
{{
  "zones": [
    {{
      "id": "zone_1",
      "label": "Short label (max 4 words)",
      "type": "danger",
      "color": "red",
      "description": "What you observe in this zone (1-2 sentences).",
      "recommendation": "One specific actionable improvement requiring no purchases.",
      "priority": 1,
      "x_percent": 10,
      "y_percent": 20,
      "width_percent": 30,
      "height_percent": 25
    }}
  ],
  "overall_score": 68,
  "summary": "Single sentence overall assessment tailored to this user."
}}

ZONE TYPES (use exactly these values):
- "danger"      color: "red"    — Immediate safety risk
- "caution"     color: "yellow" — Potential risk to monitor
- "opportunity" color: "green"  — Existing positive feature to highlight
- "suggestion"  color: "blue"   — Free improvement possible

COORDINATE RULES:
- x_percent, y_percent: top-left corner of zone (0-100 % of image width/height)
- width_percent, height_percent: zone dimensions (5-40 % each)
- Distribute zones across different areas of the image; avoid total overlap
- priority: 1 = most urgent; ascending integers
- overall_score: 0-100 rating for this user's specific needs

CRITICAL PLACEMENT RULES — violations will be rejected:
- "opportunity" (green) zones MUST cover empty or open areas: clear floor, open wall, empty shelf, window light. NEVER place them on a TV screen, sofa, occupied chair, bed, table surface, or any filled furniture.
- Zones whose label contains "floor", "open", "space", or "area" MUST have y_percent >= 45. The floor is always in the lower half of the image. If you place a floor zone near the top of the image, it will be rejected.
- Do not place any single zone entirely on top of one piece of furniture.
"""


# Module-level alias: pre-built prompt string for the default (no-profile) case.
# Imported by tests and external callers as `from backend.core.vision import VISION_PROMPT`.
VISION_PROMPT: str = build_zone_prompt("No known profile.", ["general_adult"])


# Words that indicate a zone refers to floor-level / open space.
_FLOOR_WORDS = {"floor", "open", "space", "area", "ground", "path", "walkway"}

# Furniture / object words that should never be the target of an opportunity zone.
_FURNITURE_WORDS = {
    "tv", "television", "screen", "monitor", "sofa", "couch", "armchair",
    "chair", "table", "desk", "bed", "shelf", "shelves", "wardrobe",
    "cabinet", "counter", "dresser", "bookcase", "lamp", "radiator",
}


def _validate_zones(zones: list) -> tuple[list, list]:
    """
    Post-LLM spatial sanity checks.
    Returns (valid_zones, rejected_zones).

    Rules applied:
    1. Floor/open/space zones must sit in the lower half of the image (y_percent >= 40).
    2. Opportunity (green) zones must not be labelled with furniture/object words.
    """
    valid, rejected = [], []
    for z in zones:
        label_lower = z["label"].lower()
        reject_reason = None

        # Rule 1 — floor zones must be in lower half
        if any(w in label_lower for w in _FLOOR_WORDS) and z["y_percent"] < 40:
            reject_reason = (
                f"floor/space zone '{z['label']}' placed at y={z['y_percent']:.0f}% "
                f"(must be >= 40% — floor is in lower half)"
            )

        # Rule 2 — opportunity zones must not overlap furniture labels
        if reject_reason is None and z["type"] == "opportunity":
            hit = next((w for w in _FURNITURE_WORDS if w in label_lower), None)
            if hit:
                reject_reason = (
                    f"opportunity zone '{z['label']}' references furniture word '{hit}' "
                    f"— green zones must be open space, not objects"
                )

        if reject_reason:
            print(f"[Vision] Zone rejected: {reject_reason}")
            rejected.append(z)
        else:
            valid.append(z)

    return valid, rejected


async def analyse_zones(image_b64: str, user_id: str = "default") -> dict:
    """Analyse a space image and return profile-personalised spatial zones."""
    import json
    from backend.services.profile import get_user_profile
    from backend.core.group_rules import detect_groups

    profile = get_user_profile(user_id)
    if profile:
        groups = detect_groups(profile)
        profile_text = (
            f"Name: {profile.get('name', 'Unknown')}, "
            f"Age: {profile.get('age', 'Unknown')}, "
            f"Household: {profile.get('household_members', [])}, "
            f"Accessibility needs: {profile.get('accessibility_needs', [])}, "
            f"Concerns: {profile.get('concerns', 'None')}"
        )
    else:
        groups = ["general_adult"]
        profile_text = "No known profile."

    prompt = build_zone_prompt(profile_text, groups)

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

    zones: list = []
    overall_score = 0
    summary = ""

    def _parse_raw_zones(raw: list) -> list:
        """Normalise and clamp raw zone dicts from the LLM."""
        valid_types  = {"danger", "caution", "opportunity", "suggestion"}
        valid_colors = {"red", "yellow", "green", "blue"}
        parsed = []
        for z in raw:
            parsed.append({
                "id":             str(z.get("id", f"zone_{len(parsed) + 1}")),
                "label":          str(z.get("label", "Zone"))[:50],
                "type":           z.get("type")  if z.get("type")  in valid_types  else "suggestion",
                "color":          z.get("color") if z.get("color") in valid_colors else "blue",
                "description":    str(z.get("description", "")),
                "recommendation": str(z.get("recommendation", "")),
                "priority":       int(z.get("priority", 99)),
                "x_percent":      float(max(0,  min(95, z.get("x_percent",      10)))),
                "y_percent":      float(max(0,  min(95, z.get("y_percent",      10)))),
                "width_percent":  float(max(5,  min(40, z.get("width_percent",  20)))),
                "height_percent": float(max(5,  min(40, z.get("height_percent", 20)))),
            })
        return parsed

    try:
        result       = json.loads(data.get("response", "{}"))
        raw_zones    = result.get("zones", [])
        overall_score = int(result.get("overall_score", 0))
        summary      = str(result.get("summary", ""))

        parsed       = _parse_raw_zones(raw_zones)
        zones, rejected = _validate_zones(parsed)

        # Retry once if confidence is low (overall_score < 25) or too many zones rejected
        low_confidence = overall_score < 25 or len(rejected) > len(zones)
        if low_confidence and parsed:
            print(f"[Vision] Low confidence (score={overall_score}, rejected={len(rejected)}) — retrying zone analysis.")
            async with httpx.AsyncClient(timeout=180.0) as client:
                retry_response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json=request_body,
                )
                retry_response.raise_for_status()
                retry_data   = retry_response.json()
                retry_result = json.loads(retry_data.get("response", "{}"))
                retry_parsed = _parse_raw_zones(retry_result.get("zones", []))
                retry_valid, _ = _validate_zones(retry_parsed)
                # Accept retry only if it produced more valid zones
                if len(retry_valid) > len(zones):
                    zones         = retry_valid
                    overall_score = int(retry_result.get("overall_score", overall_score))
                    summary       = str(retry_result.get("summary", summary))
                    print(f"[Vision] Retry accepted: {len(zones)} valid zones.")

    except Exception as exc:
        print(f"[Vision] Zone parse error: {exc}")

    zones.sort(key=lambda z: z["priority"])

    return {
        "zones": zones,
        "overall_score": overall_score,
        "summary": summary,
        "groups_detected": groups,
    }
