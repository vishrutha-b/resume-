# 🎯 Aura ATS — AI-Powered Resume Screening Engine

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.110.0-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/MongoDB-4.6.3-47A248?style=for-the-badge&logo=mongodb" />
  <img src="https://img.shields.io/badge/Groq_LLM-LLaMA_3.3_70B-FF6B35?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker" />
</p>

> A production-grade **Applicant Tracking System (ATS)** backend that scores, analyzes, and AI-optimizes resumes against job descriptions using an 8-layer deterministic pipeline powered by NLP, semantic embeddings, and LLM intelligence.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 **Resume Parsing** | Extracts structured data from PDF & DOCX files |
| 🧠 **8-Layer Scoring Pipeline** | Deterministic, transparent, weighted ATS scoring |
| 🔍 **Semantic Matching** | `all-MiniLM-L6-v2` sentence embeddings for contextual similarity |
| 🔑 **Keyword Intelligence** | Matched, missing, partial, implicit, and stale skill detection |
| 📊 **Readability Metrics** | Flesch-Kincaid grade, skill density, quantification rate |
| ⚡ **Impact Detection** | Flags unverified buzzwords and rewards quantified achievements |
| 🤖 **AI Optimization** | LLaMA 3.3 70B rewrites your resume for 95+ ATS scores |
| 📥 **PDF Download** | Download the AI-optimized resume as a formatted PDF |
| 🔐 **JWT Auth** | Secure user registration & login with bcrypt + JWT |
| 🗄️ **Version History** | Every re-evaluation is snapshotted for comparison |
| 🌐 **Web UI** | Built-in Jinja2 frontend with static file serving |

---

## 🏗️ Architecture

```
resume_screener/
│
├── main.py                  # FastAPI app — startup, middleware, router mounting
├── config/
│   └── settings.py          # Centralized config loaded from .env
│
├── routes/
│   ├── api.py               # Core REST API endpoints (screen, evaluate, optimize)
│   ├── auth.py              # JWT register/login/me endpoints
│   └── web.py               # Web UI routes (Jinja2 templates)
│
├── services/                # 8-Layer Scoring Pipeline
│   ├── resume_parser_v2.py  # L1: Smart Resume Parser
│   ├── jd_analyzer.py       # L2: Job Description Analyzer
│   ├── semantic_engine.py   # L3: Semantic Matching (sentence-transformers)
│   ├── keyword_engine.py    # L4: Keyword Intelligence
│   ├── experience_engine.py # L5: Experience Evaluator
│   ├── impact_detector.py   # L6: Impact & Verifiability Detector
│   ├── readability_engine.py# L6b: Readability Metrics
│   ├── score_calculator.py  # L7: Final Score Calculator
│   └── resume_optimizer.py  # AI Resume Optimizer (Groq LLM)
│
├── ats_evaluator.py         # L8: LLM Insight Generator
├── models/
│   ├── database.py          # MongoDB models (Evaluation, Version, User)
│   └── schemas.py           # Pydantic schemas for API I/O
│
├── utils/
│   ├── resume_parser.py     # PDF/DOCX text extraction
│   └── logger.py            # Centralized logging
│
├── templates/               # Jinja2 HTML templates (index, login, register)
├── static/                  # CSS & JS assets
├── uploads/                 # Temporary resume uploads (auto-cleaned)
│
├── Dockerfile               # Container image definition
├── requirements.txt         # Python dependencies
├── .env.example             # Safe environment variable template
└── .gitignore
```

---

## 🔬 The 8-Layer Scoring Pipeline

Every resume is scored through 8 independent, transparent layers:

```
L1  Smart Resume Parser     → Extracts skills, dates, structure
L2  JD Analyzer             → Identifies required/preferred skills, experience
L3  Semantic Engine         → Cosine similarity via sentence embeddings (30% weight)
L4  Keyword Intelligence    → Exact + partial + implicit skill matching (30% weight)
L5  Experience Evaluator    → Years of experience & role relevance (20% weight)
L6  Impact Detector         → Quantified achievements vs buzzwords (10% weight)
L6b Readability Engine      → Format quality, section coverage, grade level
L7  Score Calculator        → Weighted final ATS score (0–100)
L8  LLM Insight Generator   → AI-generated gaps, questions, recommendations
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- MongoDB (local or Atlas)
- A [Groq API key](https://console.groq.com) *(required for AI optimization only)*

### 1. Clone the repository

```bash
git clone https://github.com/vishrutha-b/resume-.git
cd resume-
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
DEBUG=True
HOST=0.0.0.0
PORT=8001

SECRET_KEY=your-strong-secret-key-here

MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=aura_ats

GROQ_API_KEY=your-groq-api-key-here
LLM_MODEL=llama-3.3-70b-versatile
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
python main.py
```

The API will be live at: **`http://localhost:8001`**  
Interactive docs: **`http://localhost:8001/docs`**

---

## 🐳 Running with Docker

```bash
# Build the image
docker build -t aura-ats .

# Run with environment variables
docker run -p 8001:8001 \
  -e MONGO_URI=mongodb://host.docker.internal:27017 \
  -e GROQ_API_KEY=your-key-here \
  -e SECRET_KEY=your-secret-here \
  aura-ats
```

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register a new user |
| `POST` | `/api/auth/login` | Login and receive JWT token |
| `GET` | `/api/auth/me` | Get current user info |

### Resume Evaluation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/screen_resume` | Upload resume + JD → get ATS evaluation |
| `GET` | `/api/evaluations` | List all evaluations |
| `GET` | `/api/evaluations/{id}` | Get full evaluation details |
| `PUT` | `/api/evaluations/{id}` | Re-score with new resume or JD |
| `GET` | `/api/evaluations/{id}/history` | Get version history |

### AI Optimization

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/evaluations/{id}/optimize` | Generate AI-optimized resume (requires Groq key) |
| `GET` | `/api/evaluations/{id}/optimized` | Retrieve saved optimized resume |
| `GET` | `/api/evaluations/{id}/optimized/download` | Download optimized resume as PDF |

---

## 📤 Example API Usage

### Screen a Resume

```bash
curl -X POST http://localhost:8001/api/screen_resume \
  -F "resume=@your_resume.pdf" \
  -F "job_desc=We are looking for a Python backend engineer with FastAPI and MongoDB experience..."
```

### Sample Response

```json
{
  "file_name": "your_resume.pdf",
  "evaluation_id": "abc123def456",
  "version": 1,
  "evaluation": {
    "ats_score": 78,
    "score_breakdown": {
      "semantic_match": 72.4,
      "keyword_match": 85.0,
      "experience_fit": 70.0,
      "impact_score": 65.0,
      "format_score": 90.0,
      "soft_skills": 60.0
    },
    "skill_match": {
      "matched": ["Python", "FastAPI", "MongoDB"],
      "missing": ["Docker", "Kubernetes"],
      "partial": ["REST APIs"],
      "implicit": ["Backend Development"],
      "stale": []
    },
    "readability": {
      "avg_sentence_length": 14.2,
      "reading_grade_level": 11.5,
      "skill_density_percent": 32.1,
      "quantification_rate_percent": 55.0,
      "overused_buzzwords": ["passionate", "dynamic"],
      "found_sections": ["EXPERIENCE", "SKILLS", "EDUCATION"],
      "missing_sections": ["SUMMARY"],
      "section_coverage_score": 75
    },
    "key_gaps": ["No Docker experience", "Missing Kubernetes skills"],
    "strong_points": ["Strong Python background", "FastAPI expertise"],
    "recommendations": ["Add a Professional Summary section", "Quantify your achievements"],
    "interview_questions": ["Can you walk me through your FastAPI project architecture?"],
    "domain_fit": "High",
    "experience_fit": "Medium"
  }
}
```

---

## 🔐 Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ For AI features | — | Groq API key for LLM optimization |
| `MONGO_URI` | ✅ | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB_NAME` | ✅ | `aura_ats` | MongoDB database name |
| `SECRET_KEY` | ✅ | — | JWT signing key (use a long random string) |
| `DEBUG` | ❌ | `False` | Enable debug mode & hot reload |
| `HOST` | ❌ | `0.0.0.0` | Server host address |
| `PORT` | ❌ | `8000` | Server port |
| `LLM_MODEL` | ❌ | `llama-3.3-70b-versatile` | Groq model to use |

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Web Framework** | FastAPI 0.110.0 |
| **Server** | Uvicorn (dev) / Gunicorn (prod) |
| **Database** | MongoDB via PyMongo |
| **Authentication** | JWT (python-jose) + bcrypt (passlib) |
| **Semantic AI** | `sentence-transformers` — `all-MiniLM-L6-v2` |
| **LLM** | Groq API — LLaMA 3.3 70B Versatile |
| **PDF Parsing** | pdfminer.six |
| **DOCX Parsing** | python-docx |
| **PDF Generation** | fpdf2 |
| **Validation** | Pydantic v2 |
| **Templating** | Jinja2 |
| **Containerization** | Docker |

---

## 📁 Supported File Formats

| Format | Support |
|---|---|
| `.pdf` | ✅ Full support |
| `.docx` | ✅ Full support |
| `.doc` | ❌ Not supported |
| `.txt` | ❌ Not supported |

---

## 🔒 Security Notes

- Passwords are hashed with **bcrypt** before storage
- JWT tokens expire after **30 minutes**
- Uploaded files are **deleted immediately** after text extraction
- All file uploads are validated against an extension whitelist (`.pdf`, `.docx`)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

<p align="center">Built with ❤️ by <a href="https://github.com/vishrutha-b">Vishrutha B</a></p>
