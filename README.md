# ✦ Aura — AI-Powered Spatial Companion

> *"Live better with what you have."*

Aura is designed as a **Mobile Application** that acts as a personal spatial companion. It uses your phone's camera to see your space, talks with you naturally, builds a personal profile, and gives **personalised recommendations** to improve your living space — **without suggesting purchases or major changes**.

---

## 🎯 Hackathon Alignment: AtlanTec AI Challenge 2026
**Problem Statement:** *Human Intelligence Driving Transformative Innovation*
**Focus Areas:** Healthcare (Disease & Fall Prevention, Wellbeing) & Housing (Smart Housing, Accessibility)

Aura merges human spatial intelligence with AI to transform how vulnerable demographics (elderly, mobility-impaired, children) interact with their housing environments. Rather than selling smart-home gadgets, Aura drives transformative innovation by using Edge AI to optimise the accessibility and safety of existing living spaces.

---

## 🌟 Philosophy

*"A person exists through their spatial experiences. They find true happiness and vitality only when they truly make a space their own."*

Aura goes beyond mere interior layout. The ultimate goal is to help individuals achieve the highest **spatial comfort** and experience a profound sense of belonging and peace in their environment. It ensures that people truly *live* in their space and use their time valuably through deeply personalised approaches.

While Aura is designed for everyone, **its primary mission is to alleviate the physical and psychological limitations we face in our daily environments.** Aura transforms what could be a spatial barrier (such as mobility challenges, sensory overload, or mental fatigue) into a space of healing and ease—using only the resources already available in the home.

Aura believes that this profound connection doesn't require buying new things. Instead, it helps you:

- **Rearrange** what you already own for better flow, emotional comfort, and physical accessibility
- **Repurpose** items you have in creative ways to reflect your true identity and support mental wellbeing
- **Optimise** your space for safety, natural light, and cognitive ease, directly addressing personal boundaries
- **Adapt** your environment to your household's specific needs so you can truly belong, unhindered by spatial constraints

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
│             iOS / Android App               │
│           (Native Mobile UI)                │
│         Uses device camera & sensors        │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│              FastAPI Backend                │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │  Ollama  │  │ ChromaDB │  │ NetworkX  │ │
│  │ Gemma 4  │  │Vector RAG│  │Graph RAG  │ │
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
| **Local LLM** | Ollama + Gemma 4:e4b | Vision + language (runs locally) |
| **Video** | OpenCV | Multi-frame spatial analysis |
| **Vector RAG** | ChromaDB | Profile-aware document retrieval |
| **Graph RAG** | NetworkX | Traversal of relationships (e.g. elderly -> fall risk) |
| **Time Series** | SQLite + Context | Conversation logging + pattern recognition |
| **Weather** | Met Éireann API | Real-time Irish weather |
| **Sun Position** | pvlib + Geolocation | Golden hour & direct light calculations |
| **Location** | OSM Nominatim | Profile-tailored outdoor mapping |
| **Frontend** | Mobile UI | Designed for iOS and Android displays |
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
│   │       ├── video.py     # Video upload & room labelling
│   │       ├── profile.py   # User profile management
│   │       ├── outdoor.py   # Nearby public spaces
│   │       ├── evaluate.py  # Model self-evaluation
│   │       ├── recommendations.py
│   │       └── weather.py   # Weather + sun data
│   ├── core/
│   │   ├── llm.py           # Ollama/Gemma 4 integration (Lifestyle Advisor)
│   │   ├── video.py         # OpenCV multi-frame extraction & room memory
│   │   ├── vision.py        # Photo spatial analysis
│   │   ├── rag.py           # ChromaDB knowledge retrieval
│   │   ├── outdoor.py       # Profile-aware outdoor engine
│   │   └── pattern.py       # Time series patterns
│   ├── services/
│   │   ├── weather.py       # Met Éireann API (Golden hour, sunrise)
│   │   ├── sun.py           # pvlib sun position
│   │   ├── location.py      # OpenStreetMap Nominatim
│   │   └── profile.py       # Profile management
│   ├── models/              # Pydantic data models
│   ├── db/                  # SQLite + ChromaDB
│   └── knowledge/           # RAG knowledge documents
├── frontend/
│   ├── index.html           # Mobile Webview Shell
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

## ⚙️ Advanced Engineering & Optimisations

### 1. Latency & Performance (Zero Cold-Starts)
To ensure the local LLM feels as fast as an API:
- **Server Startup Warmup** (`warmup.py`): Automatically triggers a 1-token dummy prompt upon server start to preload the model into GPU memory.
- **Persistent GPU Memory**: Configured `keep_alive=30m` so the model doesn't constantly unload/reload between requests.
- **Context Limiting**: `num_ctx=2048` ensures rapid inference times during vision-language interactions.
- **Perceived Latency to Zero**: Implementing **SSE (Server-Sent Events)** streaming for chat endpoints mimics the fluid response generation of popular cloud models.

### 2. Decoding & Anti-Hallucination
Aura serves as a reliable assistant for high-stakes domains (like child safety and elderly accessibility). Strict decoding parameter configurations prevent "over-creativity":
- `temperature`: **0.3** (Anchors model to reality) 
- `top_k`: **40** & `top_p`: **0.85** (Nucleus sampling threshold restricts wild token generation)
- `repeat_penalty`: **1.2**

### 3. Progressive Fine-Tuning & Evaluation
While Aura effectively uses zero-shot local quantized vision models, ongoing R&D focuses on:
- **Vision LLaVA/Gemma Fine-tuning:** Exploratory pipelines for fine-tuning vision models (using LoRA) on custom image datasets for niche Irish architectural quirks.
- **Time-Series ROCKET integration:** Advanced conceptual experiments employing the ROCKET algorithm for multi-variate environmental data pattern recognition.

### 4. Graph RAG & Knowledge Engineering
Traditional semantic search isn't enough for safety checking. We built:
- **NetworkX DiGraph:** A lightweight Graph RAG that traverses relationships (e.g., if a profile has ADHD $\rightarrow$ traverse to sensory overload $\rightarrow$ recommend grounding light).
- **Hybrid Retrieval:** Blending Vector (ChromaDB) with Graph traversal results in an impossibly deep, contextually-aware system prompt.

### 5. Dynamic Profiling
- **Dynamic 15+ Target Audiences**: System detects combinations like `(child under 4) + (remote worker)` and builds intersecting system prompts strictly via `group_rules.py`.
- **Sensory & Compass Aware**: Connects HTML5 device orientation (Compass heading) with `pvlib` sun position calculations to recommend where a user should sit at what time of day for optimal Vitamin D and mental focus.
- **Activity & Mood Sync**: Predefined activities (aeration, grounding) tied to mood logging (`mood_activities.py`).

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Ollama** installed and running ([ollama.com](https://ollama.com))
- **Gemma 4 Vision model** pulled via Ollama

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

### 2. Pull the Gemma 4 Model

```bash
ollama pull gemma4:e4b
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
- ✅ Works effectively mimicking a local native mobile app

---

## ⚖️ Ethical AI & Compliance (Self-Assessment)

Aura strictly adheres to the AtlanTec ethical AI principles:
1. **Fairness:** The `group_rules.py` engine adapts the model for over 15 demographics equally, ensuring recommendations are culturally and physically appropriate whether the user is a wheelchair user, a toddler's parent, or a night-shift worker.
2. **Transparency:** Aura never masks its AI nature. It provides "why" it makes a recommendation (e.g., citing the compass azimuth or weather API data).
3. **Accountability:** Hallucinations are suppressed via strict decoding (`temperature=0.3`), ensuring dangerous health/safety advice is bypassed. No medical diagnoses are attempted.
4. **Data Sovereignty:** By keeping Vector DBs, Graph DBs, and LLM inference strictly on the device (Local-first), the system is immune to mass data breaches.

---

## 👥 Team

Aura was built by an interdisciplinary team, each contributing domain expertise:

| Role | Domain | Contribution to Aura |
|------|--------|---------------------|
| **Architect** | Spatial Design & Architecture | Room layout analysis heuristics, spatial comfort criteria, accessibility standards |
| **Doctor** | Healthcare & Wellbeing | Fall prevention priorities, safety risk classification, wellbeing-focused recommendation design |
| **PhD Researcher** | Time Series & AI | Pattern recognition architecture, model evaluation pipeline, RAG system design |

All team members are actively working with AI in their respective fields. This cross-domain collaboration shaped Aura's core design decisions — from which safety risks to prioritise, to how spatial data should be interpreted, to how the AI's recommendations are validated against real clinical and architectural standards.

---

## 📄 Licence

This project is for educational and research purposes.

---

<p align="center">
  <strong>✦ Aura</strong> — Live better with what you have.
</p>
