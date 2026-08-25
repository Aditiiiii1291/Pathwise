# Pathwise Deployment & Production Readiness Guide

## 1. Overview
Pathwise is an institutional early warning and intervention platform designed for student retention. It integrates deterministic rule evaluation, explainable machine learning (Random Forest), multi-factor risk fusion, proactive notification escalation, counselling workflow management, and longitudinal trajectory effectiveness tracking.

---

## 2. Prerequisites
- **Python:** 3.12+
- **Node.js:** 20+ and npm 10+
- **Docker & Docker Compose** (Optional for containerized deployments)
- **SQLite 3**

---

## 3. Environment Variables Reference

Configure environment variables in `.env` (copy from `.env.example`):

| Variable | Scope | Type | Default / Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Backend | String | `sqlite:///./pathwise.db` (or `sqlite:////app/data/pathwise.db` in Docker) |
| `JWT_SECRET_KEY` | Backend | String | High-entropy 64-byte secret key (min 32 chars). **Required**. |
| `JWT_ALGORITHM` | Backend | String | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Backend | Integer | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Backend | Integer | `7` |
| `FRONTEND_ORIGINS` | Backend | String | Comma-separated CORS origins (e.g. `http://localhost:3000,http://localhost:5173`) |
| `PORT` | Backend | Integer | `8000` (or dynamically supplied by hosting platform) |
| `SMTP_HOST` | Backend | String | Optional SMTP host for alert dispatch |
| `SMTP_PORT` | Backend | Integer | `587` |
| `SMTP_USERNAME` | Backend | String | Optional SMTP username |
| `SMTP_PASSWORD` | Backend | String | Optional SMTP password |
| `SMTP_FROM_EMAIL` | Backend | String | `alerts@pathwise.edu` |
| `VITE_API_BASE_URL` | Frontend | String | Browser-accessible backend URL (e.g. `http://localhost:8000` or production API URL) |

> [!CAUTION]
> Never expose `JWT_SECRET_KEY`, `DATABASE_URL`, or `SMTP_PASSWORD` in frontend `VITE_*` environment variables.

---

## 4. Local Development Setup

### Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Start FastAPI ASGI server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 5. Initial Administrator & Demo Data Setup

### Option A: Interactive Administrator Setup
Create the initial institutional administrator account:
```bash
cd backend
python -m app.scripts.create_admin
```
Follow prompts to enter username (3–30 characters), display name, and password ($\ge 8$ chars with uppercase, lowercase, and digit).

### Option B: Automated / CI Setup
```bash
cd backend
python -m app.scripts.create_admin --username admin --password "YourSecureAdminPassword2026!" --display-name "System Administrator"
```

### Option C: Synthetic Academic Cohort Seeding (Public/Demo Instances)
To populate an empty database with the 500-student synthetic cohort and baseline risk assessments without creating login accounts:
```bash
cd backend
python -m app.scripts.seed_demo_data
```

*(Optional: To also initialize demo mentor and counsellor accounts for presentation testing, pass `--staff-password "<your-demo-password>"`).*

---

## 6. Docker Deployment

### Building and Running with Docker Compose
```bash
# Build images and start backend & frontend containers
docker compose build
docker compose up -d

# Verify container health
docker compose ps
```
- **Frontend URL:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000`
- **Health Check:** `http://localhost:8000/health`

### Persistent SQLite Volume
The backend container mounts a named Docker volume (`pathwise_db_data`) mapped to `/app/data`. The database is stored at `/app/data/pathwise.db`, guaranteeing data persistence across container restarts.

---

## 7. Render Cloud Deployment Guidelines

### Backend (Web Service / Docker)
1. **Environment:** Docker or Python 3.12
2. **Build Command:** `pip install -r requirements.txt` (if native Python)
3. **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables:**
   - `JWT_SECRET_KEY`: Set to a strong random 64-byte string.
   - `DATABASE_URL`: `sqlite:///./data/pathwise.db` (with Render Persistent Disk mounted at `/opt/render/project/src/data`) or ephemeral SQLite with `seed_demo_data.py`.
   - `FRONTEND_ORIGINS`: Set to your deployed Render frontend URL (e.g. `https://pathwise.onrender.com`).
5. **Health Check Path:** `/health`

### Frontend (Static Site / Web Service)
1. **Build Command:** `npm ci && npm run build`
2. **Publish Directory:** `dist`
3. **Environment Variables:**
   - `VITE_API_BASE_URL`: `https://pathwise-api.onrender.com` (your deployed backend URL)
4. **Single-Page Application (SPA) Rewrite:** Configure rewrite rule: `/*` $\rightarrow$ `/index.html` with status `200`.

---

## 8. Security & Compliance
- **Authentication:** Short-lived JWT access tokens (15-min) with rotating single-use refresh tokens (7-day).
- **Password Hashing:** Argon2id with salted iterations via `passlib`.
- **Database Safety:** Passwords, password hashes, and raw refresh tokens are never stored in plain text. Refresh tokens are stored exclusively as SHA-256 hashes (`token_hash`).
- **Institutional Headers:** All responses include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`.
- **Zero External AI Dependency:** 100% of risk scoring, rule evaluation, and explainability is calculated locally via deterministic Python and Scikit-Learn models with zero third-party AI APIs required.
