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

- **Frontend**: React (Vite), Tailwind CSS, Recharts (visualizations)
- **Backend**: FastAPI (Python), SQLAlchemy (ORM), SQLite (default local DB)
- **Data & ML**: Pandas, NumPy, openpyxl, scikit-learn (Random Forest Classifier)
- **Testing**: pytest

---

## 📂 Installation & Setup

### 1. Prerequisite Installations
Ensure you have the following installed on your machine:
- **Python 3.10+**
- **Node.js 18+ & npm 9+**
- **Git**

### 2. Clone and Setup Environment
```bash
git clone <your-repo-url> pathwise
cd pathwise
copy .env.example .env
```

### 3. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Generate Synthetic Data & Train ML Model
For development and demonstration purposes, you can generate 500 mock student profiles showing various trajectories (Improving, Stable, Gradually/Rapidly Deteriorating, Academic/Financial-only concerns):
```bash
cd ../ml
python -m data_generation.generator
python -m training.train
```

### 5. Start Backend Service
```bash
cd ../backend
uvicorn app.main:app --reload
```
The API Swagger documentation will be available at `http://127.0.0.1:8000/docs`.

### 6. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```
The client app will be running at `http://localhost:5173`.

---

## 🧪 Running Tests
Verify the installation by running backend test files:
```bash
cd backend
pytest
```

---

## 📜 License
This project is developed for hackathon purposes. Feel free to copy, modify, and self-host under public license settings.
