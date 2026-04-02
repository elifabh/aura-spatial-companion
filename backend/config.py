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

# ── Ollama / LLaVA ────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llava")

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
