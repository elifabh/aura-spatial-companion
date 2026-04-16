"""
Mood → Spotify Playlist + Scent Mapping.
Maps each of Aura's 10 mood states to a curated Spotify playlist and a
natural scent recommendation with in-room placement guidance.
"""

# ─── Scent recommendations per mood ─────────────────────────────────────────
# Each entry: scent name, brief why, and where in the room to place it.
MOOD_SCENTS = {
    "stressed": {
        "scent": "lavender",
        "placement": "near your reading chair or wherever you sit to unwind",
    },
    "tired": {
        "scent": "peppermint or citrus",
        "placement": "on the windowsill or your desk — anywhere the air moves past it",
    },
    "anxious": {
        "scent": "chamomile or lavender",
        "placement": "beside the sofa or your favourite seat",
    },
    "calm": {
        "scent": "sandalwood or vanilla",
        "placement": "on a bookshelf or side table — let it fill the room quietly",
    },
    "energetic": {
        "scent": "eucalyptus or rosemary",
        "placement": "near the entrance or on a high shelf so it greets you first",
    },
    "creative": {
        "scent": "lemon or grapefruit",
        "placement": "right beside your work area — citrus sparks the mind",
    },
    "sad": {
        "scent": "vanilla or orange blossom",
        "placement": "near your cosiest corner — somewhere you can settle in",
    },
    "angry": {
        "scent": "peppermint or eucalyptus",
        "placement": "by the window — cool scents have a calming effect on the nervous system",
    },
    "happy": {
        "scent": "jasmine or rose",
        "placement": "wherever you spend most of your time — let the joy linger",
    },
    "focused": {
        "scent": "rosemary or peppermint",
        "placement": "right on the desk beside you — both sharpen concentration",
    },
}

MOOD_SCENTS["cozy"] = MOOD_SCENTS["calm"]

# ─── Keyword → mood mapping (used by llm.py for detection) ──────────────────
# Ordered so more specific terms are tried before generic ones.
SENSORY_TRIGGER_KEYWORDS: list[tuple[str, str]] = [
    # (keyword_substring, mood)
    ("stress",      "stressed"),
    ("overwhelm",   "stressed"),
    ("tense",       "stressed"),
    ("tension",     "stressed"),
    ("anxious",     "anxious"),
    ("anxiety",     "anxious"),
    ("nervous",     "anxious"),
    ("worry",       "anxious"),
    ("panic",       "anxious"),
    ("tired",       "tired"),
    ("exhaust",     "tired"),
    ("fatigue",     "tired"),
    ("drained",     "tired"),
    ("sleepy",      "tired"),
    ("sad",         "sad"),
    ("depressed",   "sad"),
    ("unhappy",     "sad"),
    ("down",        "sad"),
    ("angry",       "angry"),
    ("anger",       "angry"),
    ("frustrat",    "angry"),
    ("annoyed",     "angry"),
    ("irritat",     "angry"),
    ("happy",       "happy"),
    ("joyful",      "happy"),
    ("excited",     "happy"),
    ("energetic",   "energetic"),
    ("energised",   "energetic"),
    ("motivated",   "energetic"),
    ("creative",    "creative"),
    ("inspired",    "creative"),
    ("focus",       "focused"),
    ("concentrat",  "focused"),
    ("productiv",   "focused"),
    ("relax",       "calm"),
    ("calm",        "calm"),
    ("peaceful",    "calm"),
    ("unwind",      "calm"),
    ("chill",       "calm"),
    ("mood",        "calm"),   # generic mood mention → calm as safe default
    ("feeling",     "calm"),
]


def detect_mood_from_text(text: str) -> str | None:
    """
    Scan free-form text for mood/sensory trigger keywords.
    Returns the first matched mood string, or None if no trigger found.
    """
    lower = text.lower()
    for keyword, mood in SENSORY_TRIGGER_KEYWORDS:
        if keyword in lower:
            return mood
    return None


# Keys match exactly the 10 moods in MOOD_PRIORITIES in mood_activities.py.
MOOD_PLAYLISTS = {
    "stressed": {
        "name": "Peaceful Meditation",
        "description": "Slow your breath and let the tension go.",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DWZd79rJ6a7lp",
    },
    "tired": {
        "name": "Morning Motivation",
        "description": "Wake up your body and spark some energy.",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DXc5e2bJhV6pu",
    },
    "anxious": {
        "name": "Anxiety Relief",
        "description": "Gentle, grounding music to ease your mind.",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DWXe9gFZP0gtP",
    },
    "calm": {
        "name": "Cozy Evenings",
        "description": "Warm, unhurried tones for a quiet evening in.",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DX4E3UdUs7fUx",
    },
    "energetic": {
        "name": "Power Hour",
        "description": "High-energy tracks to match your unstoppable mood.",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DX76Wlfdnj7AP",
    },
    "creative": {
        "name": "Creative Flow",
        "description": "Instrumental vibes to keep your ideas flowing freely.",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DWXLeA8Omikj7",
    },
    "sad": {
        "name": "Comfort Songs",
        "description": "Warm, tender music that feels like a hug.",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DX7gIoKXt0gmx",
    },
    "angry": {
        "name": "Release the Tension",
        "description": "Channel the energy and let it move through you.",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DWTggY0yqBxES",
    },
    "happy": {
        "name": "Happy Hits",
        "description": "Pure joy — turn it up and enjoy the good vibes!",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC",
    },
    "focused": {
        "name": "Deep Focus",
        "description": "Minimal distractions, maximum concentration.",
        "url": "https://open.spotify.com/playlist/37i9dQZF1DWZeKCadgRdKQ",
    },
}

# Convenience alias so the cozy activity category also resolves correctly.
MOOD_PLAYLISTS["cozy"] = MOOD_PLAYLISTS["calm"]


def get_playlist_for_mood(mood: str) -> dict | None:
    """Return the Spotify playlist dict for a given mood, or None if not found."""
    return MOOD_PLAYLISTS.get(mood.lower())


def get_sensory_context(mood: str) -> str | None:
    """
    Return a prompt-ready sensory hint block for the given mood.
    Provides the Spotify playlist and scent info for Aura to weave into its reply.
    Returns None if the mood is unrecognised.
    """
    mood = mood.lower()
    playlist = MOOD_PLAYLISTS.get(mood)
    scent = MOOD_SCENTS.get(mood)
    if not playlist and not scent:
        return None

    lines = ["[SENSORY SUGGESTIONS — weave these naturally into your reply, like a friend would mention them in passing]"]
    if playlist:
        lines.append(
            f"Music: suggest the '{playlist['name']}' Spotify playlist — {playlist['url']} — "
            "mention the link so they can tap it. Don't say 'I suggest', just drop it in conversationally."
        )
    if scent:
        lines.append(
            f"Scent: mention {scent['scent']} placed {scent['placement']}. "
            "Tie it to a specific spot in the room if you know it, e.g. 'a little lavender near your reading corner'."
        )
    lines.append("Keep it warm and brief — one sentence per sensory cue, not a list.")
    return "\n".join(lines)
