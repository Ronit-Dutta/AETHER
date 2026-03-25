# 🛸 Project AETHER — Autonomous Exoplanet Mission Control

**🔗 Live Dashboard:** [https://Ronit-Dutta.github.io/AETHER](https://Ronit-Dutta.github.io/AETHER)

> **AETHER** = Autonomous Exoplanet Terrain & Habitability Evaluation Report

An AI-powered autonomous system that scans NASA's Exoplanet Archive 24/7, calculates habitability scores using real astrophysics, generates speculative biology reports via Google Gemini, and visualizes alien worlds in interactive 3D.

---

## 🌟 Features

- **Autonomous Daily Audit** — Scans NASA's archive for new exoplanet discoveries
- **Habitability Intelligence Engine** — Calculates habitable zones using Kopparapu et al. (2013) formulas
- **Speculative Evolution Generator** — AI creates scientifically-grounded hypothetical lifeforms
- **3D Mission Control Dashboard** — Three.js procedural planet rendering based on real data
- **"Laptop-Off" Automation** — Runs 24/7 via GitHub Actions

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Brain** | Google Gemini 2.0 Flash |
| **Data Source** | NASA Exoplanet Archive (TAP API) |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **Frontend** | HTML/CSS/JS + Three.js |
| **Automation** | GitHub Actions (daily cron) |

## 📁 Project Structure

```
AETHER/
├── .env                          # API keys (never commit!)
├── .gitignore
├── .github/workflows/
│   └── daily-mission.yml         # GitHub Actions automation
├── backend/
│   ├── config.py                 # Environment config loader
│   ├── nasa_fetcher.py           # NASA Exoplanet Archive API
│   ├── habitability_engine.py    # Scientific habitability scoring
│   ├── gemini_engine.py          # Gemini AI bio-report generator
│   ├── database.py               # Supabase CRUD + schema
│   ├── mission_control.py        # Main orchestrator script
│   └── requirements.txt
└── frontend/
    ├── index.html                # Mission Control Dashboard
    ├── styles.css                # Premium dark theme
    └── app.js                    # Three.js engine + Supabase client
```

## 🚀 Quick Start

### 1. Setup Database
1. Go to [Supabase Dashboard](https://supabase.com) → Your AETHER project
2. Open **SQL Editor**
3. Copy the SQL from `backend/database.py` (printed when you run it) and execute it
4. This creates all required tables: `planets`, `bio_reports`, `mission_logs`, `discovery_stats`

### 2. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Run Your First Mission
```bash
cd backend
python mission_control.py 10
```
This will scan 10 planets, calculate habitability, generate AI bio-reports, and save to Supabase.

### 4. View the Dashboard
Open `frontend/index.html` in your browser. The dashboard loads demo data instantly, and once your database has real data, it will display that instead.

### 5. Deploy Automation (Optional)
1. Push code to GitHub
2. Go to Settings → Secrets → Actions
3. Add: `SUPABASE_URL`, `SUPABASE_KEY`, `GEMINI_API_KEY`
4. The daily scan runs automatically at midnight UTC!

## 📸 Screenshots

The dashboard features:
- Animated starfield background
- Gradient AETHER logo with spinner loading screen
- Discovery Gallery with 3D rotating planet cards
- Interactive 3D Viewer with mouse orbit controls
- Detailed planet modal with bio-reports and hypothetical lifeforms

---

*Built with ❤️ for IIT Patna*
