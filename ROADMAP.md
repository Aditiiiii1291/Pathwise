# 🎯 MASTER ENGINEERING ROADMAP: PATHWISE
## Early Warning & Intervention Intelligence for Student Retention
### AI-Based Drop-Out Prediction and Counselling System (Problem Statement 10)

This roadmap serves as the master blueprint to build **Pathwise** from absolute zero to a complete, hackathon-ready implementation. Each phase is self-contained with explicit dependencies, inputs, outputs, file changes, and testing steps to enable structured execution.

---

## 📂 REPOSITORY STRUCTURE

All development should follow this standard directory structure. No code or configuration files should sit outside of these directories except for base-level configs (`.gitignore`, `.env.example`, etc.).

```
pathwise/
│
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # API endpoints (v1)
│   │   ├── core/             # Configuration, DB connection, security
│   │   ├── models/           # SQLAlchemy database schemas
│   │   ├── schemas/          # Pydantic schemas (request/response validation)
│   │   ├── crud/             # Database queries & updates
│   │   └── services/         # Rule engine, Risk Fusion, notification helpers
│   └── requirements.txt
│
├── frontend/                 # React Application (Vite-scaffolded)
│   ├── src/
│   │   ├── components/       # Shared UI components (Charts, Tables, Layout)
│   │   ├── pages/            # View pages (Overview, Student Profile, Rules, Table)
│   │   ├── context/          # State management (auth, preferences)
│   │   ├── utils/            # Formatter helpers, API callers
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── tailwind.config.js
│
├── ml/                       # Machine Learning Model Pipeline
│   ├── data_generation/      # Synthetic data generator scripts
│   ├── training/             # Model training & serialization code
│   └── models/               # Saved pickle/joblib binary model files
│
├── data/                     # Data stores (CSV samples, templates)
│   ├── raw/                  # Uploaded source spreadsheets (simulated)
│   └── templates/            # Downloadable template files for ingestion
│
├── tests/                    # Unit and Integration Tests
│   ├── backend/              # pytest files for API & logic
│   ├── ml/                   # Tests for model training & evaluation
│   └── frontend/             # Optional Vitest tests for UI components
│
├── docs/                     # Documentation and Pitch assets
├── README.md
├── ROADMAP.md                # This file
├── .gitignore
└── .env.example              # Template configuration variables
```

---

## 🚩 DEVELOPMENT MILESTONES (GITHUB)

We define the project lifecycle using the following GitHub Milestones. Do not skip milestones or commit unverified changes to the main branch.

- **`v0.1-foundation`**: Project scaffolded, Git configured, virtual environments active, README/ROADMAP published.
- **`v0.2-database`**: SQLite database design complete, migrations configured, and local connection active.
- **`v0.3-synthetic-data`**: Core data generator capable of exporting 500+ students with diverse trend profiles.
- **`v0.4-data-ingestion`**: Upload endpoints ready, mapping CSVs/XLSX into database successfully.
- **`v0.5-feature-engineering`**: Calculation of temporal slopes, acceleration, and decline variables.
- **`v0.6-rule-engine`**: Configurable rule engine mapping parameters to deterministic risk tiers.
- **`v0.7-ml-engine`**: ML model trained, serialized, and generating explainable dropout probabilities.
- **`v0.8-risk-fusion`**: Rules + ML combination logic executing, outputting unified scores and trends.
- **`v0.9-api`**: Complete backend endpoints documented in OpenAPI (Swagger) UI.
- **`v1.0-dashboard`**: React dashboard reflecting overview metrics, tables, and filters.
- **`v1.1-intervention`**: Interventions logged, tracked, and recalculated in the database.
- **`v1.2-testing`**: Complete pytest coverage of analytical algorithms and integration points.
- **`v1.3-demo-ready`**: End-to-end simulation verified, ready for submission.

---

## 🚀 ROADMAP PHASES

---

### PHASE 0 — Project Planning & Environment Setup

#### Objective
Establish local environment prerequisites, initialize the version control repository, and finalize requirements parameters.

#### Why This Phase
Ensures that all developers on the team run matching dependency configurations and prevents pipeline breakdown due to missing tools.

#### Technologies
- Git & GitHub
- Python (v3.10+)
- Node.js (v18+) & npm (v9+)
- VS Code (or preferred IDE)

#### Work To Do
- [ ] Install system packages: Python 3.10+, Node.js (current LTS), Git client.
- [ ] Create a local repository folder named `pathwise`.
- [ ] Create a GitHub repository (private/public) for collaboration.
- [ ] Initialize Git in the local repository (`git init`).
- [ ] Set up main branch protection and define branching convention: `main` (production), `develop` (integration), `feature/*` (active development).
- [ ] Populate `.gitignore` with common Python (`__pycache__`, `.venv`), Node (`node_modules`, `dist`), and Database (`*.db`, `*.sqlite3`) configurations.
- [ ] Generate `.env.example` mapping key configurations: `DATABASE_URL`, `PORT`, `JWT_SECRET`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`.
- [ ] Publish the initial commit to remote repository.

#### Files / Modules
- `/pathwise/`
  - `.gitignore`
  - `.env.example`
  - `README.md`
  - `ROADMAP.md`

#### Inputs
- Initial product plan, OS installation binaries.

#### Outputs
- Functional, clean GitHub repository with working `.gitignore` and `.env.example`.

#### Testing
- Execute `git status` to verify tracked vs untracked paths.
- Execute `python --version` and `node --version` to verify correct runtimes.

#### Exit Criteria
- GitHub repository matches local directory. No dependency caches, IDE files, or DB file paths committed.

#### Dependencies
- None (First Phase).

---

### PHASE 1 — Repository & Application Foundation

#### Objective
Scaffold directory structures and initialize development environments for both backend and frontend applications.

#### Why This Phase
Ensures backend dependencies and frontend scripts build properly before introducing complex logic.

#### Technologies
- FastAPI
- React, Vite
- Tailwind CSS

#### Work To Do
- [ ] Generate backend repository layout.
- [ ] Initialize Python Virtual Environment: `python -m venv backend/.venv`.
- [ ] Create initial `backend/requirements.txt` with dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `pandas`, `openpyxl`, `scikit-learn`, `pytest`, `python-multipart`.
- [ ] Install requirements: `pip install -r backend/requirements.txt`.
- [ ] Create a base FastAPI file `backend/app/main.py` containing a root health-check endpoint `GET /health`.
- [ ] Scaffold frontend project: `npm create vite@latest frontend -- --template react` in the root folder.
- [ ] Set up Tailwind CSS inside the `frontend` folder using standard config files.
- [ ] Create a root `.env` file containing local configurations (copy of `.env.example`).
- [ ] Add a utility script or configuration in React to fetch from backend localhost.

#### Files / Modules
- `backend/requirements.txt`
- `backend/app/main.py`
- `frontend/package.json`
- `frontend/src/App.jsx`
- `frontend/tailwind.config.js`
- `.env`

#### Inputs
- Phase 0 repository structure.

#### Outputs
- Working local environments for backend and frontend. FastAPI app running locally on `http://127.0.0.1:8000` and React app running on `http://localhost:5173`.

#### Testing
- Run FastAPI local server: `uvicorn app.main:app --reload` from `backend/` and assert `{"status": "healthy"}` at `/health`.
- Boot React development server: `npm run dev` from `frontend/` and load page on browser.

#### Exit Criteria
- Successful HTTP handshakes between React application and FastAPI server via basic health routes without CORS errors.

#### Dependencies
- Phase 0.

---

### PHASE 2 — Database Design & Data Models

#### Objective
Define the SQL data structures using an Object Relational Mapper (ORM) to represent student paths, academic records, and intervention cycles.

#### Why This Phase
A robust database design ensures that feature engineering, uploads, rule evaluation, and outcome tracking can write to structured records with constraints.

#### Technologies
- Python
- SQLAlchemy
- SQLite

#### Work To Do
- [ ] Design DB Schemas matching ORM classes in `backend/app/models/`:
  - **`Student`**: Holds primary info (`id`, `roll_number`, `name`, `department`, `semester`, `guardian_name`, `guardian_phone`, `guardian_email`, `mentor_id`, `created_at`). Add unique index on `roll_number`.
  - **`Mentor`**: Account table (`id`, `name`, `email`, `department`, `phone`).
  - **`AttendanceRecord`**: Weekly track (`id`, `student_id` FK, `week_number`, `month`, `total_classes`, `attended_classes`, `percentage` derived, `created_at`).
  - **`MarksRecord`**: Academic track (`id`, `student_id` FK, `subject_name`, `exam_type` [enum: test1, test2, test3, final], `max_marks`, `obtained_marks`, `attempt_number`, `created_at`).
  - **`FeeRecord`**: Financial metadata (`id`, `student_id` FK, `semester`, `total_fee`, `paid_amount`, `due_date`, `status` [enum: paid, partial, pending], `created_at`).
  - **`RiskSnapshot`**: Evaluated scores (`id`, `student_id` FK, `computed_at`, `rule_score`, `ml_probability`, `final_score`, `risk_tier` [enum: low, medium, high, critical], `trend` [enum: improving, stable, gradually_det, rapidly_det], `factors_json`, `feature_imp_json`, `recommendations`).
  - **`Intervention`**: Logged history (`id`, `student_id` FK, `mentor_id` FK, `date`, `type` [enum: counselling, academic_support, fee_verification, attendance_plan, other], `notes`, `risk_score_before`, `followup_date`, `status` [enum: scheduled, completed, cancelled], `outcome` [enum: pending, improved, unchanged, escalated], `risk_score_after`, `created_at`).
  - **`RuleConfig`**: Configurations (`id`, `department` nullable, `config_json`, `updated_at`, `updated_by`).
  - **`Notification`**: Alert trail (`id`, `student_id` FK, `type` [enum: email, sms], `recipient_type` [enum: mentor, guardian], `recipient_email`, `subject`, `body`, `sent_at`, `status` [enum: sent, failed, pending]).
- [ ] Write DB connection initialization modules inside `backend/app/core/database.py` with SQLite defaults.
- [ ] Configure automatic execution of Table Creation via metadata schemas at backend startup (or set up Alembic migrations if time permits).

#### Files / Modules
- `backend/app/core/database.py`
- `backend/app/models/student.py`
- `backend/app/models/mentor.py`
- `backend/app/models/attendance.py`
- `backend/app/models/marks.py`
- `backend/app/models/fee.py`
- `backend/app/models/risk.py`
- `backend/app/models/intervention.py`
- `backend/app/models/config.py`
- `backend/app/models/notification.py`

#### Inputs
- Technical architecture parameters.

#### Outputs
- Data schema models initialized. Local SQLite database file `pathwise.db` generated automatically.

#### Testing
- Write a short Python script under `backend/app/tests/test_db_conn.py` that connects to SQLite, writes a mock Student and Mentor, and queries them to verify FK constraints.

#### Exit Criteria
- Successful initialization, write, and deletion test cycles across all designed entity tables.

#### Dependencies
- Phase 1.

---

### PHASE 3 — Synthetic Dataset Generator

#### Objective
Develop a script that creates realistic student trajectories over time to simulate a production-like environment with varied risk trends.

#### Why This Phase
Enables offline development and testing of predictive models, early warnings, and visualizations without needing access to sensitive institutional records.

#### Technologies
- Python
- NumPy
- Pandas

#### Work To Do
- [ ] Implement `ml/data_generation/generator.py`.
- [ ] Define generation metrics: target 500 students, 5 departments (CSE, ECE, ME, CE, EEE), 8 semesters.
- [ ] Define the 6 Student Trajectories:
  - **Improving**: Starts with low scores/attendance, but goes up after week 4 (simulating intervention).
  - **Stable**: Consistently high attendance (85%+), passing grades, no backlogs.
  - **Gradually Deteriorating**: Slow, steady fall in attendance (1-2% per week) and gradual test decline.
  - **Rapidly Deteriorating**: Sharp drop in attendance (80% down to 50% in 4 weeks), failing test scores.
  - **Academic Distress Only**: Good attendance but dropping test performance (75% to 40%) + new backlogs.
  - **Financial Context Only**: Stable academic performance but late fees.
- [ ] Output four distinct, matching CSV tables mimicking isolated school systems:
  - `attendance.csv` (cols: `student_id`, `week_number`, `attended_classes`, `total_classes`)
  - `marks.csv` (cols: `student_id`, `subject_name`, `exam_type`, `max_marks`, `obtained_marks`, `attempt_number`)
  - `fees.csv` (cols: `student_id`, `semester`, `total_fee`, `paid_amount`, `due_date`, `status`)
  - `students_roster.csv` (cols: `student_id`, `roll_number`, `name`, `department`, `semester`, `guardian_name`, `guardian_phone`, `guardian_email`, `mentor_id`, `dropout_label`)
- [ ] Export these tables into a designated test assets folder `ml/data/`.

#### Files / Modules
- `ml/data_generation/generator.py`
- `ml/data/students_roster.csv`
- `ml/data/attendance.csv`
- `ml/data/marks.csv`
- `ml/data/fees.csv`

#### Inputs
- Phase 2 schemas and trajectory models.

#### Outputs
- Four CSV files containing cohesive data for 500 students.

#### Testing
- Verify that every `student_id` in the attendance, marks, and fee files matches a primary key in `students_roster.csv`. Assert values are within logical bounds (e.g. attendance percentage between 0 and 100).

#### Exit Criteria
- CSV generation pipeline completes in under 5 seconds with zero orphaned student IDs.

#### Dependencies
- Phase 2.

---

### PHASE 4 — Data Ingestion & Validation

#### Objective
Build the parser endpoints to import CSV files, validating their format and columns before inserting clean records into the database.

#### Why This Phase
Institutions supply data in inconsistent spreadsheet formats. The ingestion pipeline must align and validate inputs to prevent invalid database writes.

#### Technologies
- FastAPI
- Pandas
- openpyxl
- Pydantic

#### Work To Do
- [ ] Define Pydantic request models in `backend/app/schemas/upload.py` to validate CSV headers.
- [ ] Build file mapping parser logic in `backend/app/services/parser.py`.
- [ ] Implement smart column mapper (auto-matching: "Roll Number", "roll_no", "Student ID", "ID", "attendance_%", "attendance_percentage").
- [ ] Define validation constraints (reject uploads if essential columns are missing or if values are malformed).
- [ ] Implement validation rules:
  - Attendance must be integer counts or floats between 0 and 100.
  - Marks must not exceed max marks value.
  - Fees must contain valid numbers.
- [ ] Capture rows with parsing errors and return them to the user in a JSON diagnostic report, rather than failing the entire batch import.
- [ ] Create basic ingestion routes in `backend/app/api/endpoints/uploads.py` that handle binary files.

#### Files / Modules
- `backend/app/schemas/upload.py`
- `backend/app/services/parser.py`
- `backend/app/api/endpoints/uploads.py`

#### Inputs
- Synthetic CSV data files.

#### Outputs
- HTTP endpoints capable of processing and storing file uploads, returning structured success counts and validation summaries.

#### Testing
- Write test assertions:
  - Test valid import processes.
  - Test import rejection with missing columns (e.g. missing `student_id`).
  - Test validation recovery with partially malformed rows.

#### Exit Criteria
- The parser accepts the generated synthetic files, detects columns correctly, rejects malformed test CSVs, and writes valid records to SQLite.

#### Dependencies
- Phase 3.

---

### PHASE 5 — Student Data Fusion

#### Objective
Correlate the raw data streams from independent spreadsheets using the student ID/Roll Number as the common key, creating a consolidated student record.

#### Why This Phase
Risk indicators do not exist in isolation. Fusing attendance, test marks, attempts, and fees allows the model to analyze compounding indicators together.

#### Technologies
- Python
- SQLAlchemy
- Pandas

#### Work To Do
- [ ] Write database queries in `backend/app/crud/student.py` that fetch a student's full historical record (attendance sequence, tests, fees) in a single profile.
- [ ] Implement a fusion service `backend/app/services/fusion.py` that takes raw database entries and converts them into a consolidated structured dictionary.
- [ ] Handle data gaps gracefully (e.g., student has attendance records but no exam marks yet).
- [ ] Format the fused payload to contain:
  - Core student demographic info
  - Sorted chronological weekly attendance array
  - Chronological test scores grouped by subject
  - Fee payments and backlog variables.

#### Files / Modules
- `backend/app/crud/student.py`
- `backend/app/services/fusion.py`

#### Inputs
- Populated SQLite database.

#### Outputs
- A backend module that returns a consolidated, unified profile for any selected student roll number.

#### Testing
- Query a specific student ID and verify that the output dictionary accurately matches all associated rows in the `attendance_records`, `marks_records`, and `fee_records` tables.

#### Exit Criteria
- A unified student data structure can be retrieved for all 500 synthetic students in less than 50ms average latency.

#### Dependencies
- Phase 4.

---

### PHASE 6 — Temporal Feature Engineering

#### Objective
Calculate time-series indicators (slopes, declines, acceleration, patterns) from fused attendance and academic data.

#### Why This Phase
Emerging risk is identified through deteriorating trajectories over time, rather than isolated low scores.

#### Technologies
- Python
- NumPy
- Pandas (Linear Regression / Polyfit)

#### Work To Do
- [ ] Implement feature generator library in `backend/app/services/features.py`.
- [ ] Create helper methods to compute **Attendance Trend Features**:
  - `attendance_current`: Latest recorded attendance percentage.
  - `attendance_slope`: Linear regression slope over the last 6 weeks (using `numpy.polyfit`).
  - `attendance_decline_pp`: Total percentage points lost since historical peak.
  - `attendance_consecutive_decline`: Count of consecutive weeks with declining attendance.
  - `attendance_acceleration`: Rate of change of the slope (second derivative) to detect if attendance decline is speeding up.
- [ ] Create helper methods to compute **Academic Trend Features**:
  - `marks_current_avg`: Average score of the most recent internal tests.
  - `marks_slope`: Average slope of marks over sequential assessments.
  - `marks_recent_vs_previous`: Ratio of average of last 2 assessments to prior assessments.
  - `marks_consecutive_failures`: Number of sequential assessments below passing threshold.
  - `marks_failed_subject_count`: Number of distinct subjects currently failed.
- [ ] Create helper methods to compute **Backlog & Fee Context Features**:
  - `backlog_trend`: Numeric trend indicating if uncleared backlogs are growing semester-over-semester.
  - `fee_overdue_terms`: Number of overdue term cycles.
  - `fee_pct_unpaid`: Unpaid fee ratio.

#### Files / Modules
- `backend/app/services/features.py`

#### Inputs
- Fused student data dictionary.

#### Outputs
- Structured feature record containing raw values and calculated temporal slope metrics.

#### Testing
- Write a unit test using static arrays to assert correct outputs:
  - An attendance sequence `[90, 80, 70, 60]` should output a negative slope and 3 consecutive decline periods.
  - An academic sequence `[40, 50, 60, 70]` should show a positive slope (improving trajectory).

#### Exit Criteria
- Slope, decline, and acceleration indicators compute accurately for all students, with clean handling of edge cases (e.g. students with only 1 week of data).

#### Dependencies
- Phase 5.

---

### PHASE 7 — Explainable Rule Engine

#### Objective
Implement a rule-based classification engine that calculates risk scores using transparent, customizable parameters.

#### Why This Phase
Ensures institutional users can configure rule thresholds and weights to match their policy requirements (e.g., matching the official institute attendance limit).

#### Technologies
- Python
- Pydantic

#### Work To Do
- [ ] Define configurable parameters (weights, thresholds) in `backend/app/schemas/rules.py` with standard configurations:
  - Attendance threshold (e.g. < 75% triggers alert)
  - Attendance slope threshold (e.g. dropping > 5% weekly)
  - Marks average threshold (e.g. < 40%)
  - Weight vectors (e.g. Attendance 30%, Marks 25%, Backlogs 15%, Fees 10%, Trends 20%).
- [ ] Write the evaluator engine in `backend/app/services/rules.py`.
- [ ] Map each feature input to a normalized factor score (0 to 100).
- [ ] Multiply factor scores by weights to compute `rule_score` (0 to 100).
- [ ] Generate natural language explanations for rule violations:
  - *“Attendance declined by 15 percentage points in the last month.”*
  - *“Fee payment delay detected (verification recommended).”*
- [ ] Implement configurations to load and update rules dynamically from database configs.

#### Files / Modules
- `backend/app/schemas/rules.py`
- `backend/app/services/rules.py`

#### Inputs
- Engineered temporal student features.

#### Outputs
- Engine outputting a deterministic score, classification, and text explanation.

#### Testing
- Pass a mock student profile through the engine and assert that changing weights or thresholds in the configuration config changes the output score as expected.

#### Exit Criteria
- The rule engine evaluates configurations dynamically, computes weighted risk scores, and generates corresponding natural language descriptions of the contributing factors.

#### Dependencies
- Phase 6.

---

### PHASE 8 — ML Prediction Engine

#### Objective
Train a Random Forest classifier using scikit-learn on the synthetic dataset to predict student dropout probability.

#### Why This Phase
The machine learning model identifies non-linear combinations of risk indicators that standard rules might miss.

#### Technologies
- Python
- Scikit-learn
- Pandas
- Joblib

#### Work To Do
- [ ] Build the training script in `ml/training/train.py`.
- [ ] Load the synthetic files and extract the engineered temporal features (Phases 3 and 6).
- [ ] Preprocess features (impute missing values, scale numeric columns).
- [ ] Run a train-test split (80/20 split) on the student dataset.
- [ ] Train a Random Forest Classifier model.
- [ ] Extract feature importance array (`model.feature_importances_`) to identify the most predictive indicators.
- [ ] Save the trained model pipeline as a joblib binary `ml/models/dropout_detector.joblib`.
- [ ] Document model metrics: print training accuracy, precision, recall, F1, and confusion matrix.
- [ ] **Crucial**: Include a warning in the model metadata stating that synthetic accuracy is for demo purposes and must be updated with real institutional records in production.

#### Files / Modules
- `ml/training/train.py`
- `ml/models/dropout_detector.joblib`
- `ml/models/metadata.json`

#### Inputs
- Fused temporal features and synthetic datasets.

#### Outputs
- Serialized machine learning pipeline file ready for inference.

#### Testing
- Verify model training outputs are valid. Ensure the model outputs a float probability between 0.0 and 1.0 for test cases.

#### Exit Criteria
- Serialized model binary is generated, can be loaded in Python, and outputs a classification probability vector without runtime errors.

#### Dependencies
- Phase 6.

---

### PHASE 9 — Risk Fusion Engine

#### Objective
Build the fusion system that blends the rule-based output with the ML dropout probability to determine the final risk tier and trend indicator.

#### Why This Phase
Combining transparent rules with predictive machine learning provides both institutional logic and data-driven predictions.

#### Technologies
- Python

#### Work To Do
- [ ] Implement fusion class in `backend/app/services/fusion_engine.py`.
- [ ] Load the trained model binary at startup.
- [ ] Define the blending formula:
  `final_score = (rule_weight * rule_score) + (ml_weight * ml_probability * 100)`
  (Use default weights: rule_weight = 0.5, ml_weight = 0.5).
- [ ] Categorize the resulting combined score into risk tiers:
  - **`LOW`** (score < 25)
  - **`MEDIUM`** (25 to 50)
  - **`HIGH`** (51 to 75)
  - **`CRITICAL`** (76+)
- [ ] Determine the Early Warning Trend label:
  - **`RAPIDLY_DETERIORATING`**: Strong negative slope (e.g. attendance dropping > 5% weekly or marks dropping > 8% per exam) and accelerating.
  - **`GRADUALLY_DETERIORATING`**: Moderate negative slope.
  - **`STABLE`**: Minor variations (within +/- 1%).
  - **`IMPROVING`**: Consistent positive slope.
- [ ] Map the computed values to the SQLAlchemy `RiskSnapshot` model schema.

#### Files / Modules
- `backend/app/services/fusion_engine.py`

#### Inputs
- Configurable rules, model binary, and raw student features.

#### Outputs
- Consolidated risk assessment profile (`risk_score`, `risk_tier`, `trend`, `probability`).

#### Testing
- Assert that a student profile with low attendance (60%) and declining grades is classified as `CRITICAL` risk with a `RAPIDLY_DETERIORATING` trend.
- Assert that labels specify "Predicted Dropout Probability: X%" rather than "Model Confidence: X%".

#### Exit Criteria
- The fusion engine accurately resolves scores and outputs the unified risk tier and trend classification.

#### Dependencies
- Phase 7, Phase 8.

---

### PHASE 10 — Explanation & Recommendation Engine

#### Objective
Expose the most influential risk factors for each student and generate actionable, supportive recommendations.

#### Why This Phase
Mentors need clear reasons why a student was flagged, along with helpful guidance on how to support them.

#### Technologies
- Python
- Scikit-learn (Feature Importances)

#### Work To Do
- [ ] Create explanation mapper script: `backend/app/services/explainer.py`.
- [ ] Extract prediction-level feature contributions (e.g. multiply model feature importances by the student's normalized feature deviation).
- [ ] Sort factors to identify the top 4 drivers (e.g. 1. Attendance decline, 2. Failing grades, 3. Late fees).
- [ ] Define helper functions to map these top factors to supportive recommendations:
  - Attendance decline -> *“Initiate attendance recovery discussion. Assess potential schedule conflicts.”*
  - Marks decline -> *“Suggest academic tutoring or peer study groups.”*
  - Backlogs -> *“Develop study plan for clearing outstanding subjects.”*
  - Late fees -> *“Verify fee-related circumstances and check eligibility for payment plans.”* (Avoid financial distress assumptions).
  - Multiple factors -> *“Schedule immediate mentor counselling session.”*
- [ ] Return these details in a structured JSON schema.

#### Files / Modules
- `backend/app/services/explainer.py`

#### Inputs
- Risk Fusion output and feature deviations.

#### Outputs
- Structured JSON list containing top risk factors and actionable, supportive recommendations.

#### Testing
- Verify that a profile flagged for late fees only returns a warning to *"Verify fee-related circumstances"* and does not make assumptions about their financial situation.

#### Exit Criteria
- Explanations and recommendations are generated automatically based on the top risk factors.

#### Dependencies
- Phase 9.

---

### PHASE 11 — FastAPI Backend

#### Objective
Expose the system features through a clean API, documenting the request and response schemas in the Swagger UI.

#### Why This Phase
Connects the backend data processing, model predictions, and rule configuration to the React frontend.

#### Technologies
- FastAPI
- Uvicorn
- Pydantic

#### Work To Do
- [ ] Create route endpoints in `backend/app/api/endpoints/`:
  - **Uploads**: `POST /api/uploads`, `GET /api/uploads/history`.
  - **Students**: `GET /api/students` (paginated, with search, department, semester, risk, and trend filters), `GET /api/students/{id}` (full profile).
  - **Analytics**: `GET /api/dashboard/overview` (returns aggregate metrics for risk tiers and trends), `GET /api/dashboard/departments`, `GET /api/dashboard/effectiveness`.
  - **Rules**: `GET /api/rules` (current rules config), `PUT /api/rules` (update rule configurations).
  - **Interventions**: `POST /api/interventions` (log new), `GET /api/interventions/{student_id}` (history), `PUT /api/interventions/{id}` (update outcome).
  - **Notifications**: `POST /api/notifications` (trigger alert), `GET /api/notifications` (history).
- [ ] Enable CORS middleware in `backend/app/main.py` to allow requests from the React frontend.
- [ ] Implement global error handling middleware to capture exceptions and return structured JSON responses.

#### Files / Modules
- `backend/app/api/api.py` (root router)
- `backend/app/api/endpoints/students.py`
- `backend/app/api/endpoints/dashboard.py`
- `backend/app/api/endpoints/rules.py`
- `backend/app/api/endpoints/interventions.py`
- `backend/app/api/endpoints/notifications.py`

#### Inputs
- Core service modules and API route parameters.

#### Outputs
- Functional HTTP API endpoints with interactive documentation at `/docs`.

#### Testing
- Run test suites using `pytest` and `fastapi.testclient.TestClient` to verify endpoints return valid JSON and appropriate status codes (e.g. 200 OK, 400 Bad Request, 444 Not Found).

#### Exit Criteria
- All core API endpoints are defined, documented, and successfully retrieve data from the database.

#### Dependencies
- Phase 10.

---

### PHASE 12 — React Frontend & Dashboard

#### Objective
Build the dashboard UI using React, displaying key overview metrics, student list filters, and detailed profile pages.

#### Why This Phase
Provides a clean, intuitive interface for mentors and administrators to monitor student progress and manage support interventions.

#### Technologies
- React (Vite)
- Tailwind CSS
- Recharts (Charts Library)

#### Work To Do
- [ ] Scaffold layouts and routing structure using React Router in `frontend/src/`.
- [ ] **Overview Page**:
  - Top KPI cards (Total Students, At-Risk count, Critical count, Improved count).
  - Early warning trend board (Rapidly Deteriorating, Gradually Deteriorating, Stable, Improving).
  - Charts: Risk distribution (pie chart), department breakdowns (bar chart), and intervention outcomes (donut chart).
- [ ] **Student Risk Table**:
  - Interactive table displaying Student ID, Name, Department, Semester, Risk Tier (colour-coded badge), Trend, Dropout Probability, and summary metrics.
  - Interactive filters: Search bar, Department dropdown, Semester dropdown, Risk Tier filter, and Trend filter.
- [ ] **Student Profile View**:
  - Detailed student overview displaying risk assessment metrics and trends.
  - Interactive charts: Attendance trends (weekly line chart) and academic marks trend line chart.
  - Clear risk explanation card outlining why the student was flagged.
  - Supportive, actionable recommendation card.
  - Intervention history panel displaying log notes and status timeline.
- [ ] **Rule Configuration Page**:
  - Settings panel with sliders to adjust weights and rule thresholds.
  - Rule modification preview displaying simulated updates.

#### Files / Modules
- `frontend/src/components/Sidebar.jsx`
- `frontend/src/components/KPICards.jsx`
- `frontend/src/components/OverviewCharts.jsx`
- `frontend/src/pages/DashboardOverview.jsx`
- `frontend/src/pages/StudentTable.jsx`
- `frontend/src/pages/StudentProfile.jsx`
- `frontend/src/pages/RuleConfig.jsx`

#### Inputs
- Dynamic API endpoints.

#### Outputs
- Interactive React dashboard application fetching and displaying live backend data.

#### Testing
- Verify dashboard visuals, responsive UI grid, table filtering, page navigation, and chart rendering across standard screen sizes.

#### Exit Criteria
- Dashboard displays metric cards, renders trend line charts, supports student search, and fetches live configuration values.

#### Dependencies
- Phase 11.

---

### PHASE 13 — Notifications

#### Objective
Develop the alert pipeline to send email notifications to mentors and guardians when emerging risk is detected.

#### Why This Phase
Automated alerts ensure that mentors and guardians are notified early, enabling timely support before minor issues compound.

#### Technologies
- Python
- SMTP / Mock email handlers

#### Work To Do
- [ ] Create the notification service `backend/app/services/notifier.py`.
- [ ] Design email templates:
  - **Mentor Template**: Detailed warning list, risk score summary, and recommended action steps.
  - **Guardian Template**: Supportive, non-alarmist message focusing on student support and attendance recovery. (Avoid terms like *“ML prediction”* or *“dropout risk”*).
- [ ] Implement SMTP email dispatcher using configurations from variables.
- [ ] Create mock notifier fallback logic for local testing without active mail servers.
- [ ] Implement notification logging to record alert history and delivery status in the database.

#### Files / Modules
- `backend/app/services/notifier.py`
- `backend/app/schemas/notification.py`

#### Inputs
- Dynamic student profiles, configuration settings, and contact directories.

#### Outputs
- Notification service capable of dispatching emails and logging alert history.

#### Testing
- Assert notification logs correctly capture email details.
- Verify template variables resolve correctly and display expected student information in output messages.

#### Exit Criteria
- Email alerts are generated automatically, handle template formatting correctly, and update delivery status log entries in the database.

#### Dependencies
- Phase 11.

---

### PHASE 14 — Counselling & Intervention Workflow

#### Objective
Develop the intervention tracking system, allowing mentors to log counselling sessions, assign support plans, and record follow-ups.

#### Why This Phase
Ensures that risk identification is followed by structured support, creating an active feedback loop between prediction and intervention.

#### Technologies
- Python
- React
- SQLAlchemy

#### Work To Do
- [ ] Create DB writing modules: `backend/app/crud/intervention.py`.
- [ ] Expose endpoint `POST /api/interventions` to log new interventions with fields: Type, Notes, and Follow-up Date. Set the baseline risk score.
- [ ] Build front-end intervention dialog card inside the Student Profile page.
- [ ] Expose status update endpoint `PUT /api/interventions/{id}` to log follow-up results.
- [ ] Update student status flags in database tables to reflect scheduled support plans.

#### Files / Modules
- `backend/app/crud/intervention.py`
- `frontend/src/components/InterventionModal.jsx`
- `frontend/src/components/InterventionHistory.jsx`

#### Inputs
- Active student profiles and mentor authentication context.

#### Outputs
- Database tracking models and frontend forms for managing counselling records.

#### Testing
- Log a mock intervention session, verify database write updates the history list, and confirm status fields display scheduled dates.

#### Exit Criteria
- Mentors can log counselling notes, set follow-up dates, and view intervention history in the dashboard UI.

#### Dependencies
- Phase 12.

---

### PHASE 15 — Intervention Effectiveness & Follow-up

#### Objective
Develop the analytics feedback loop to measure student progress after support interventions have been logged.

#### Why This Phase
Tracks observed risk changes over time, helping administrators evaluate whether counselling and academic support plans are successfully helping students.

#### Technologies
- Python
- SQLAlchemy
- Recharts

#### Work To Do
- [ ] Write feedback processor query logic in `backend/app/services/feedback_loop.py`.
- [ ] Compare current risk scores with historical values recorded when the intervention was initialized.
- [ ] Classify progress outcomes:
  - **`IMPROVED`**: Combined risk score decreased.
  - **`UNCHANGED`**: Combined risk score remains stable.
  - **`ESCALATED`**: Combined risk score increased.
- [ ] Build global aggregation endpoints: `GET /api/dashboard/effectiveness` (returns counts for Improved, Unchanged, and Escalated cases).
- [ ] Render intervention outcome charts in the React dashboard using Recharts.
- [ ] **Crucial**: Ensure all charts use descriptive phrasing like *"observed risk reduction"* rather than claiming direct causal relationships.

#### Files / Modules
- `backend/app/services/feedback_loop.py`
- `frontend/src/components/EffectivenessChart.jsx`

#### Inputs
- Saved risk snapshots and logged student interventions.

#### Outputs
- Analytic data and charts showing changes in student risk levels after support interventions.

#### Testing
- Simulate a follow-up calculation: update a student's attendance from 60% to 85% after logging an intervention, and verify their risk trend transitions to `IMPROVING`.

#### Exit Criteria
- The dashboard displays clear charts showing the distribution of student progress outcomes (Improved, Unchanged, Escalated).

#### Dependencies
- Phase 14.

---

### PHASE 16 — Testing, Security & Reliability

#### Objective
Implement comprehensive unit testing and security configurations to protect student data and ensure system stability.

#### Why This Phase
Validates that calculations, rules, and APIs function reliably under edge-case conditions prior to deployment.

#### Technologies
- Pytest
- Pydantic validation

#### Work To Do
- [ ] Configure `tests/` directory with test runner settings.
- [ ] Write integration test classes covering core system logic:
  - **Ingestion**: Test file uploads with missing IDs, duplicate student rows, invalid data types, and malformed files.
  - **Rule Engine**: Test weight adjustments, out-of-bound threshold rules, and config updates.
  - **Temporal Features**: Test calculation of negative slopes, positive slopes, and single-week history limitations.
  - **Fusion Engine**: Test predictions for deteriorating students and ensure late fees without academic issues do not trigger critical risk ratings.
- [ ] Implement API route security: validate user inputs, use secure environment variables, and avoid hardcoding access credentials.
- [ ] Verify sensitive student and guardian contact details are handled securely.

#### Files / Modules
- `tests/conftest.py`
- `tests/backend/test_ingestion.py`
- `tests/backend/test_features.py`
- `tests/backend/test_rules.py`
- `tests/backend/test_fusion.py`

#### Inputs
- Complete backend application and test CSV files.

#### Outputs
- Automated test scripts validating core features, rule engine, and data processing routes.

#### Testing
- Run `pytest tests/` in the terminal and confirm all test files compile and pass successfully.

#### Exit Criteria
- Automated testing executes successfully with zero errors across all core functional test suites.

#### Dependencies
- Phase 15.

---

### PHASE 17 — Final Integration

#### Objective
Connect the frontend and backend systems, run end-to-end integration tests, and configure production-ready settings.

#### Why This Phase
Ensures the client and server work together seamlessly with reliable database reads and error handling in a production-like setup.

#### Technologies
- Python
- React
- CORS Configurations

#### Work To Do
- [ ] Clean up configuration variables and configure CORS middleware in FastAPI to allow cross-origin requests.
- [ ] Update frontend API paths to use production environment variables.
- [ ] Run build test: build the React frontend using `npm run build` and ensure Vite outputs static assets to `dist/` without compilation warnings.
- [ ] Test the entire system workflow: Upload spreadsheet data, verify dashboard charts render, click a student profile, and log an intervention.
- [ ] Implement database backup steps for SQLite files.

#### Files / Modules
- `backend/app/main.py`
- `frontend/.env.production`

#### Inputs
- Complete codebase assets.

#### Outputs
- Production-ready build artifacts and verified client-server integration.

#### Testing
- Run end-to-end test scripts from a clean environment, verifying that data imports, rule updates, and dashboard visualizations function correctly without manual intervention.

#### Exit Criteria
- React static assets build successfully, and the system runs smoothly end-to-end on localhost without console warnings.

#### Dependencies
- Phase 16.

---

### PHASE 18 — Demo, Documentation & Hackathon Submission

#### Objective
Prepare documentation, clean up sample spreadsheets, and draft the demonstration narrative for the hackathon submission.

#### Why This Phase
A clear presentation and detailed documentation ensure judges can easily install the app, run the code, and understand the project's value proposition.

#### Technologies
- Markdown
- Git

#### Work To Do
- [ ] Write detailed setup instructions in `README.md` (installation steps, running backend servers, building frontend apps, and training models).
- [ ] Populate `data/templates/` folder with dummy CSV templates (`attendance_template.csv`, `marks_template.csv`, `fees_template.csv`) to help users test imports.
- [ ] Write down the presentation steps:
  1. Show disconnected spreadsheets representing the current challenge.
  2. Upload files and show columns mapping automatically.
  3. View the dashboard metrics showing risk trends and warning levels.
  4. View a student profile showing attendance charts and risk factors.
  5. Send email notification and log a counselling session.
  6. Adjust weight sliders on the rule configuration page.
  7. Show updated student status reflecting progress outcomes.
- [ ] Push all final updates, clean configurations, and testing documents to the main branch.

#### Files / Modules
- `README.md`
- `data/templates/attendance_template.csv`
- `data/templates/marks_template.csv`
- `data/templates/fees_template.csv`

#### Inputs
- Fully completed project repository.

#### Outputs
- Final repository code, templates, and setup documentation.

#### Testing
- Follow the instructions in `README.md` step-by-step in a clean directory to verify the installation setup works correctly.

#### Exit Criteria
- Code matches submission requirements, README instructions are clear, and demo datasets are ready.

#### Dependencies
- Phase 17.

---

## 📋 MASTER BUILD ORDER CHECKLIST

Follow this checklist step-by-step. Do not start a phase until all previous phases are complete.

- [ ] **Phase 0 — Planning**: Setup local envs, initialize Git, configure branch protection.
- [ ] **Phase 1 — Foundation**: Scaffold files, verify frontend-backend local connection.
- [ ] **Phase 2 — Database**: Create SQLAlchemy models, database connection files.
- [ ] **Phase 3 — Synthetic Data**: Generate CSV files containing student trajectories.
- [ ] **Phase 4 — Ingestion**: Build column-mapping engine and upload routes.
- [ ] **Phase 5 — Data Fusion**: Group disparate tables by Roll Number into unified profiles.
- [ ] **Phase 6 — Feature Engineering**: Calculate trends, slopes, and consecutive declines.
- [ ] **Phase 7 — Rule Engine**: Implement configurable thresholds and weights.
- [ ] **Phase 8 — ML Engine**: Train model binary, extract feature importance metrics.
- [ ] **Phase 9 — Risk Fusion**: Fuse rules with ML probabilities into risk tiers and trends.
- [ ] **Phase 10 — Explanation**: Generate natural-language summaries and recommendations.
- [ ] **Phase 11 — Backend**: Build FastAPI endpoints and verify Swagger docs.
- [ ] **Phase 12 — Frontend**: Build dashboard, tables, and student profile views.
- [ ] **Phase 13 — Notifications**: Create email alerts using template modules.
- [ ] **Phase 14 — Counselling**: Log intervention sessions and follow-up alerts.
- [ ] **Phase 15 — Intervention Analytics**: Calculate observed risk trends post-intervention.
- [ ] **Phase 16 — Testing/Security**: Write test files for ingestion, rules, and backend APIs.
- [ ] **Phase 17 — Integration**: Verify integration, run end-to-end tests.
- [ ] **Phase 18 — Final Demo**: Publish setup guide and prepare demo narrative.
