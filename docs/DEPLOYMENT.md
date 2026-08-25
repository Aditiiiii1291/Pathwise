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

## 7. Render Cloud Deployment Guidelines (with Persistent PostgreSQL)

### 1. Provision Managed PostgreSQL on Render
1. In Render Dashboard, click **New +** $\rightarrow$ **PostgreSQL**.
2. **Name:** `pathwise-db` (or desired name).
3. **Region:** Select the same region as your backend Web Service (e.g. *Oregon (US West)*).
4. **Plan:** Free or Starter.
5. Click **Create Database**.
6. Once provisioned, copy the **Internal Database URL** (if backend is on Render) or **External Database URL**.
   *(Render URLs starting with `postgres://` or `postgresql://` are automatically handled and normalized by Pathwise).*

### 2. Configure Backend Web Service
1. In Render Dashboard, open your backend service (`pathwise-92ht`).
2. Go to **Environment** tab.
3. Configure the following environment variables:
   - `DATABASE_URL`: `<paste-your-render-postgresql-url>`
   - `JWT_SECRET_KEY`: `<generate-a-secure-64-byte-token>`
   - `FRONTEND_ORIGINS`: `https://pathwise-1-sibf.onrender.com` (your deployed frontend URL)
4. Click **Save Changes** $\rightarrow$ Render will automatically redeploy the backend.
5. Verify health: `GET https://pathwise-92ht.onrender.com/health` returns `{"status": "healthy"}`.
   *(Tables are automatically initialized upon startup via `init_db()`).*

### 3. Initialize Initial Administrator & Academic Dataset
Open the **Shell** tab in your Render backend Web Service (or run via SSH):
1. **Create Initial Administrator Account:**
   ```bash
   python -m app.scripts.create_admin
   ```
   Follow the interactive prompts to set your secure username and password.
2. **Seed Synthetic Academic Cohort (Optional):**
   ```bash
   python -m app.scripts.seed_demo_data
   ```
   Populates 500 synthetic student records, attendance, marks, fees, and baseline risk snapshots into PostgreSQL.

### 4. Configure Frontend Static Site
1. In Render Dashboard, open your frontend service (`pathwise-1-sibf`).
2. Go to **Environment** tab:
   - `VITE_API_BASE_URL`: `https://pathwise-92ht.onrender.com`
3. Click **Save Changes** and trigger **Manual Deploy** $\rightarrow$ **Clear build cache & deploy**.
4. Configure SPA Rewrite Rule: In **Redirects/Rewrites**, add `/*` $\rightarrow$ `/index.html` with action `Rewrite`.
5. Open `https://pathwise-1-sibf.onrender.com`, log in with your administrator account, and verify all data and sessions persist permanently across backend redeployments.

---

## 8. Security & Compliance
- **Authentication:** Short-lived JWT access tokens (15-min) with rotating single-use refresh tokens (7-day).
- **Password Hashing:** Argon2id with salted iterations via `passlib`.
- **Database Safety:** Passwords, password hashes, and raw refresh tokens are never stored in plain text. Refresh tokens are stored exclusively as SHA-256 hashes (`token_hash`).
- **Institutional Headers:** All responses include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`.
- **Zero External AI Dependency:** 100% of risk scoring, rule evaluation, and explainability is calculated locally via deterministic Python and Scikit-Learn models with zero third-party AI APIs required.
