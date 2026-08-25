# 🎯 Pathwise

> **Early Warning & Intervention Intelligence for Student Retention**  
> AI-Based Drop-Out Prediction and Counselling System (Problem Statement 10)

Pathwise is a self-hostable, lightweight web application designed for public technical institutes to help detect at-risk student dropouts weeks before term-end failures, explain the risk factors transparently, provide mentors with actionable recommendations, and track the effectiveness of counselling interventions over time.

---

## 🚀 Core Value Proposition

```
DETECT → EXPLAIN → INTERVENE → TRACK
```

1. **DETECT**: Ingest separate spreadsheets (attendance, marks, backlogs, fee status) and merge them into a unified student timeline to identify deteriorating performance trends.
2. **EXPLAIN**: Expose why a student is flagged using an interpretable risk fusion engine (Rules + ML), listing the primary risk contributors.
3. **INTERVENE**: Give mentors supportive, non-diagnostic counselling recommendation checklists.
4. **TRACK**: Create a feedback loop to record intervention details, schedule follow-ups, and calculate if student risk levels decrease over time.

---

## 🛠️ Technology Stack

- **Frontend**: React (Vite), Tailwind CSS, Lucide Icons, Recharts
- **Backend**: FastAPI (Python 3.12), SQLAlchemy (ORM), SQLite
- **Authentication**: JWT Access Tokens + Rotating Refresh Tokens, Argon2id password hashing, RBAC (`ADMIN`, `MENTOR`, `COUNSELLOR`)
- **Data & ML**: Pandas, NumPy, openpyxl, Scikit-Learn (Random Forest Dropout Classifier)
- **Containerization**: Docker (multi-stage build), Docker Compose, Nginx
- **Testing**: pytest (194 automated test cases)

---

## 📂 Quick Start & Setup

### 1. Prerequisites
- **Python 3.12+**
- **Node.js 20+ & npm 10+**
- **Docker & Docker Compose** (Optional)

### 2. Clone and Configure
```bash
git clone <your-repo-url> pathwise
cd pathwise
copy .env.example .env
```
Set a strong `JWT_SECRET_KEY` in `.env` (min 32 characters):
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Initialize Database & Seed Cohort Data
To seed a 500-student synthetic cohort with baseline risk assessments:
```bash
python -m app.scripts.seed_demo_data
```

To create the initial institutional administrator account:
```bash
python -m app.scripts.create_admin
```

### 5. Start Backend Server
```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
API Documentation is live at `http://127.0.0.1:8000/docs` and Health at `http://127.0.0.1:8000/health`.

### 6. Start Frontend Application
```bash
cd ../frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🐳 Docker Deployment

To run the complete platform in isolated containers:
```bash
docker compose build
docker compose up -d
```
- **Frontend App:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000`

---

## 🧪 Automated Testing

Execute the complete regression test suite (194 tests covering rules, ML, fusion, interventions, notifications, and security):
```bash
cd backend
python -m pytest tests -v
```

---

## 📖 Deployment Documentation
For production cloud deployment guidelines (e.g. Render, Railway, Docker), persistent volume configuration, and security controls, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## 📜 License
This project is developed for hackathon and institutional retention research purposes.
