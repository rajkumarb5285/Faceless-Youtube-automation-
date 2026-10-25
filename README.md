# Faceless YouTube Multi-Agent Studio

> Autonomous YouTube video production studio powered by **LangGraph**, **FastAPI**, **React (Vite)**, **FFmpeg**, and **Whisper**, built according to the *Faceless YouTube Multi-Agent Studio: Build Blueprint (v1)*.

---

## 🌟 Key Features

1. **Deterministic 14-Step Production Pipeline (LangGraph)**:
   - **Strategist**: Selects outlier topics based on demand vs competitor saturation; enforces repetition control ($<0.85$ cosine similarity).
   - **Researcher & Verifier**: Mines primary T1/T2 sources; audits facts into a strict claims table (verified / weak / rejected).
   - **Planner & Scriptwriter**: Act structure with 20–30s retention maps and strict claim citations (Traceability must be 10/10). Automatically rejects banned AI clichés.
   - **Critic (Quality Gate 1)**: Autonomous scoring on hook strength, originality, pacing, and clarity. Up to 3 rewrite iterations before human intervention.
   - **Visual Planner & Fallback Ladder**: Dynamically selects visual formats (Stock $\rightarrow$ Motion Still $\rightarrow$ Chart $\rightarrow$ Text Card).
   - **Voice Director & Whisper**: Scene-by-scene TTS generation with speech error verification (WER/CER $<5\%$) and precise word-level subtitle sync.
   - **Deterministic FFmpeg Renderer**: 1080p long-form / 9:16 Shorts with audio ducking (-14 LUFS) and animated captions.
   - **QA Gate (Quality Gate 2)**: Automated checks for black frames, silence pauses, loudness out-of-range, and human review sign-off.
   - **Metadata & Publisher**: Pillow thumbnail generation, SEO descriptions with complete source URLs, and scheduled YouTube Data API v3 uploads.
   - **Analyst**: Retention curve feedback loop that continuously updates the channel's style guide rules.

2. **Native Indic Language Support**:
   - Native script generation for Hindi (hi-IN), Tamil (ta-IN), Telugu (te-IN), Kannada (kn-IN), Bengali (bn-IN), Marathi (mr-IN), Gujarati (gu-IN), Punjabi (pa-IN), and Hinglish.
   - Sarvam AI Bulbul v3 TTS integration with pace and pronunciation dictionary controls.
   - Noto fonts & HarfBuzz complex-script shaping for captions.

3. **Autonomy Ladder & Emergency Kill Switch**:
   - **L0**: Manual review at every stage.
   - **L1 (Default)**: Script and final video require human sign-off.
   - **L2**: Gates pause only if QA automated checks detect issues.
   - **L3**: Fully autonomous.
   - **Kill Switch**: Instant global publishing pause button accessible in the UI.

---

## 🚀 Quickstart with Docker Compose

Ensure Docker and Docker Compose are installed, then run:

```bash
# 1. Clone & copy environment settings
cp .env.example .env

# 2. Spin up MongoDB, Redis, Qdrant, FastAPI backend, Celery worker, and React dashboard
docker-compose up --build
```

- **Dashboard UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Qdrant Vector DB**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

## 🛠️ Local Development (Without Docker)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

*(Optional) Start Celery worker in a separate terminal:*
```bash
celery -A app.worker.celery worker --loglevel=info
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000).

---

## 📂 Repository Structure

```
facelessvideo/
├── docker-compose.yml              # MongoDB, Redis, Qdrant, API, Worker, Frontend
├── .env.example                    # All API keys, database URLs, and configuration
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── config.py               # Pydantic BaseSettings
│       ├── schemas.py              # Blueprint Pydantic schemas (Section 17.1 & 21.6)
│       ├── db.py                   # MongoDB, Redis & Qdrant connectors with local fallback
│       ├── tools.py                # Web search, readability scrapers, ffprobe, CER/WER metrics
│       ├── llm.py                  # Claude / OpenAI / Gemini abstraction & JSON parser
│       ├── tts.py                  # Sarvam AI Bulbul v3, ElevenLabs & local audio synthesizers
│       ├── render.py               # Deterministic FFmpeg engine, audio ducking & auto-checks
│       ├── nodes.py                # 14 LangGraph production nodes
│       ├── graph.py                # LangGraph StateGraph & conditional routing
│       ├── worker.py               # Celery worker tasks & async thread execution
│       ├── main.py                 # FastAPI endpoints, WebSockets & static media host
│       └── prompts/                # Standardized system prompts (Section 6 & 17)
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── src/
    │   ├── api.js                  # REST API & WebSocket client
    │   ├── App.jsx                 # Studio dashboard container
    │   ├── index.css               # Modern dark-mode aesthetic styling
    │   └── components/
    │       ├── Header.jsx          # Kill switch, channel selector, new video trigger
    │       ├── PipelineTimeline.jsx# 14-stage LangGraph progress visualizer
    │       ├── ScriptEditorModal.jsx# Quality Gate 1 human review & claim status chips
    │       ├── QAPlayerModal.jsx   # Quality Gate 2 video player with diagnostic checks
    │       └── ChannelsManager.jsx # Indic voice & channel profile manager
```

---

## 📄 License
MIT License. Built for autonomous, high-quality, traceable video creation.
