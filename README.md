# ✦ Aura — AI-Powered Spatial Companion

> *"Live better with what you have."*

Aura is a **local-first Progressive Web App (PWA)** that acts as a personal spatial companion. It uses your device camera to see your space, talks with you naturally, builds a personal profile, and gives **personalised recommendations** to improve your living space — **without suggesting purchases or major changes**.

---

## 🌟 Philosophy

Aura believes that better living doesn't require buying new things. Instead, it helps you:

- **Rearrange** what you already own for better flow and comfort
- **Repurpose** items you have in creative ways
- **Optimise** your space for safety, natural light, and accessibility
- **Adapt** your environment to your household's specific needs

---

## 👥 Who Is Aura For?

| User | How Aura Helps |
|------|---------------|
| 🧒 **A mother with an 18-month hyperactive child** | Safety suggestions, activity zones, child-proofing with existing items |
| 👴 **A 70-year-old with mobility issues** | Accessibility improvements, fall prevention, reachability optimisations |
| 🎨 **A preschool teacher planning activities** | Creative space setups, rotation ideas, sensory environment tips |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│                  PWA Frontend               │
│           (HTML / CSS / JS)                 │
│         Runs on mobile browser              │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│              FastAPI Backend                │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │  Ollama  │  │ ChromaDB │  │  SQLite   │ │
│  │  LLaVA   │  │   RAG    │  │  Logging  │ │
│  └──────────┘  └──────────┘  └───────────┘ │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │        External APIs (free)          │   │
│  │  Met Éireann · pvlib · OpenStreetMap │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
         🔒 All data stays local
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python (FastAPI) | REST API server |
| **Local LLM** | Ollama + LLaVA | Vision + language (runs locally) |
| **RAG** | ChromaDB | Irish health & demographic knowledge base |
| **Time Series** | SQLite | Conversation logging + pattern recognition |
| **Weather** | Met Éireann API | Real-time Irish weather (free) |
| **Sun Position** | pvlib | Solar calculations (local library) |
| **Location** | OpenStreetMap Nominatim | Geographic context (free) |
| **Frontend** | PWA (HTML/CSS/JS) | Runs on any mobile browser |
| **Privacy** | Privacy by Design | Zero cloud dependency |

---

## 📁 Project Structure

```
Aura/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration settings
│   ├── api/
│   │   └── routes/          # API endpoints
│   │       ├── chat.py      # Natural conversation
│   │       ├── camera.py    # Spatial vision analysis
│   │       ├── profile.py   # User profile management
│   │       ├── recommendations.py
│   │       └── weather.py   # Weather + sun data
│   ├── core/
│   │   ├── llm.py           # Ollama/LLaVA integration
│   │   ├── vision.py        # Image analysis
│   │   ├── rag.py           # ChromaDB knowledge retrieval
│   │   └── pattern.py       # Time series patterns
│   ├── services/
│   │   ├── weather.py       # Met Éireann API
│   │   ├── sun.py           # pvlib sun position
│   │   ├── location.py      # OpenStreetMap
│   │   └── profile.py       # Profile management
│   ├── models/              # Pydantic data models
│   ├── db/                  # SQLite + ChromaDB
│   └── knowledge/           # RAG knowledge documents
├── frontend/
│   ├── index.html           # PWA shell
│   ├── manifest.json        # PWA manifest
│   ├── sw.js                # Service worker
│   ├── css/styles.css       # Design system
│   ├── js/
│   │   ├── app.js           # Main controller
│   │   ├── api.js           # API client
│   │   ├── camera.js        # Camera module
│   │   └── chat.js          # Chat module
│   └── assets/              # Icons & images
├── data/                    # Local SQLite DB (gitignored)
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Ollama** installed and running ([ollama.com](https://ollama.com))
- **LLaVA model** pulled via Ollama

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd Aura

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Pull the LLaVA Model

```bash
ollama pull llava
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work for local setup)
```

### 4. Run the Server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Open in Browser

Navigate to `http://localhost:8000` on your phone or desktop.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🔒 Privacy by Design

Aura is built with **zero cloud dependency**:

- ✅ All AI inference runs locally via Ollama
- ✅ All data stored in local SQLite and ChromaDB
- ✅ No telemetry, no analytics, no tracking
- ✅ Camera images are processed locally and never uploaded
- ✅ External API calls (weather, location) use free, no-auth endpoints
- ✅ Works offline after initial load (PWA)

---

## 📄 Licence

This project is for educational and research purposes.

---

<p align="center">
  <strong>✦ Aura</strong> — Live better with what you have.
</p>
