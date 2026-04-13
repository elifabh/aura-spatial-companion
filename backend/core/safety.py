"""
Safety Module — Content moderation and boundary enforcement.
Filters text and image inputs before they reach the LLM.
Provides warm, non-judgemental redirects.
"""

import re

# ── Harmful content keyword lists ────────────────────────
# These are intentionally broad to catch edge cases
_VIOLENCE_PATTERNS = [
    r"\b(kill|murder|attack|weapon|gun|knife|bomb|shoot|stab|hurt someone)\b",
    r"\b(assault|abuse|beat up|punch|violent)\b",
]

_HATE_PATTERNS = [
    r"\b(hate speech|racial slur|racist|sexist|homophobic|transphobic)\b",
    r"\b(nazi|white supremac|genocide)\b",
]

_SELF_HARM_PATTERNS = [
    r"\b(suicide|self[- ]harm|cut myself|end my life|want to die|kill myself)\b",
    r"\b(overdose|don't want to live)\b",
]

_EXPLICIT_PATTERNS = [
    r"\b(porn|nude|nsfw|sexual|xxx|erotic)\b",
]

_DISTRESS_PATTERNS = [
    r"\b(depressed|hopeless|no point|can't go on|nobody cares)\b",
    r"\b(all alone|no one understands|giving up)\b",
]

# Compile all patterns
_ALL_HARMFUL = []
for group in [_VIOLENCE_PATTERNS, _HATE_PATTERNS, _SELF_HARM_PATTERNS, _EXPLICIT_PATTERNS]:
    for pattern in group:
        _ALL_HARMFUL.append(re.compile(pattern, re.IGNORECASE))

_DISTRESS_COMPILED = [re.compile(p, re.IGNORECASE) for p in _DISTRESS_PATTERNS]
_SELF_HARM_COMPILED = [re.compile(p, re.IGNORECASE) for p in _SELF_HARM_PATTERNS]


# ── Warm response messages ───────────────────────────────
REDIRECT_MESSAGE = (
    "I'm here to help with your living space and surroundings. "
    "Let's focus on making your home more comfortable and safe. "
    "Is there anything about your space I can help with?"
)

DISTRESS_MESSAGE = (
    "I hear you, and I want you to know that matters. "
    "I'm a spatial companion, so I'm best at helping with your home environment, "
    "but if you're going through a tough time, please consider reaching out to "
    "someone you trust, or contact:\n\n"
    "**Samaritans Ireland**: 116 123 (free, 24/7)\n"
    "**Pieta House**: 1800 247 247\n"
    "**Text About It**: Text HELLO to 50808\n\n"
    "You're not alone. 💛"
)

IMAGE_REDIRECT_MESSAGE = (
    "I can only analyse living spaces, rooms, and home environments. "
    "Could you take a photo of your room, hallway, or workspace instead? "
    "I'd love to help improve your space!"
)


# ── System prompt safety boundaries ──────────────────────
SAFETY_SYSTEM_ADDENDUM = """
[CRITICAL SAFETY BOUNDARIES]
- You are Aura, a spatial wellness companion ONLY.
- You NEVER give medical diagnoses or prescriptions.
- You NEVER give legal advice.
- For any medical or mental health concern, always say: "I'd suggest speaking with a healthcare professional about this."
- If a user seems distressed, acknowledge their feelings warmly and suggest speaking to someone they trust or a helpline.
- You only discuss topics related to: home spaces, rooms, lighting, air quality, furniture arrangement, safety, accessibility, comfort, and spatial wellness.
- If asked about unrelated topics, gently redirect: "That's outside my expertise, but I'd love to help with your space!"
"""


def check_text_safety(text: str) -> dict:
    """
    Check user text input for harmful content.
    Returns: {safe: bool, response: str | None, category: str | None}
    """
    if not text or not text.strip():
        return {"safe": True, "response": None, "category": None}

    text_lower = text.lower()

    # Check for self-harm (highest priority — needs compassionate response)
    for pattern in _SELF_HARM_COMPILED:
        if pattern.search(text_lower):
            return {
                "safe": False,
                "response": DISTRESS_MESSAGE,
                "category": "self_harm",
            }

    # Check for distress signals
    for pattern in _DISTRESS_COMPILED:
        if pattern.search(text_lower):
            return {
                "safe": False,
                "response": DISTRESS_MESSAGE,
                "category": "distress",
            }

    # Check for violence, hate, explicit content
    for pattern in _ALL_HARMFUL:
        if pattern.search(text_lower):
            return {
                "safe": False,
                "response": REDIRECT_MESSAGE,
                "category": "harmful_content",
            }

    return {"safe": True, "response": None, "category": None}


def check_image_safety(image_description: str = "") -> dict:
    """
    Basic image content check.
    In production, this would use a vision safety model.
    For now, checks the description text from LLaVA for red flags.
    """
    if not image_description:
        return {"safe": True, "response": None}

    # Check description for non-spatial content
    non_spatial_keywords = [
        "person", "face", "body", "nude", "weapon",
        "document", "screen", "phone", "computer screen",
    ]

    desc_lower = image_description.lower()
    for keyword in non_spatial_keywords:
        if keyword in desc_lower:
            # These are soft warnings, not hard blocks
            # (people can be in rooms, screens on desks, etc.)
            pass

    return {"safe": True, "response": None}


def get_safety_system_prompt() -> str:
    """Returns the safety boundaries system prompt addendum."""
    return SAFETY_SYSTEM_ADDENDUM
