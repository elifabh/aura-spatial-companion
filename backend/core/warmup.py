"""
Model Warmup — Cold start elimination.
Sends a tiny prompt to Ollama on startup so the model loads into GPU memory.
Subsequent requests are then significantly faster (~3x improvement).
"""

import httpx
from backend.config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    OLLAMA_OPTIONS, OLLAMA_KEEP_ALIVE, OLLAMA_NUM_CTX,
)


async def warmup_model():
    """Send a minimal prompt to pre-load the model into GPU memory."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": "Hello.",
                    "stream": False,
                    "options": {**OLLAMA_OPTIONS, "num_ctx": OLLAMA_NUM_CTX, "num_predict": 1},
                    "keep_alive": OLLAMA_KEEP_ALIVE,
                },
            )
            if response.status_code == 200:
                print(f"[Aura] Model '{OLLAMA_MODEL}' warmed up successfully — GPU ready.")
            else:
                print(f"[Aura] Warmup returned status {response.status_code}")
    except Exception as e:
        print(f"[Aura] Model warmup skipped (Ollama may not be running): {e}")
