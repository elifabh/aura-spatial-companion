"""
Aura Configuration
All settings are local-first — zero cloud dependency.
"""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = BASE_DIR / "backend" / "knowledge"

# ── SQLite ─────────────────────────────────────────────
SQLITE_DB_PATH = DATA_DIR / "aura.db"

# ── ChromaDB ───────────────────────────────────────────
CHROMA_PERSIST_DIR = str(DATA_DIR / "chroma")

# ── Ollama / Gemma 4 E4B ──────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")

# ── Decoding (anti-hallucination) ─────────────────────
OLLAMA_OPTIONS = {
    "temperature": 0.3,       # Low = more factual, less creative hallucination
    "top_k": 40,              # Restrict to top-40 tokens
    "top_p": 0.85,            # Nucleus sampling threshold
    "repeat_penalty": 1.2,    # Discourage repetitive outputs
}

# ── Performance ───────────────────────────────────────
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")  # Keep model warm in GPU
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "2048"))   # Smaller ctx = faster

# ── External APIs (all free / local) ──────────────────
MET_EIREANN_API_URL = "https://prodapi.metweb.ie/observations"
OPENSTREETMAP_NOMINATIM_URL = "https://nominatim.openstreetmap.org"

# ── Server ────────────────────────────────────────────
HOST = os.getenv("AURA_HOST", "0.0.0.0")
PORT = int(os.getenv("AURA_PORT", "8000"))
DEBUG = os.getenv("AURA_DEBUG", "true").lower() == "true"

# ── Privacy ───────────────────────────────────────────
# All data stays local. No telemetry, no cloud sync.
PRIVACY_MODE = True
