<div align="center">
  <img src="./frontend/logo.png" alt="CareerPilot-AI Logo" width="420" />
  <p><strong>An intelligent career workspace for JD matching, application tracking, interview review, and skill growth.</strong></p>
</div>

---

CareerPilot-AI is an intelligent career workspace for managing the full job application process. It helps users analyze target job descriptions against their resume, optimize resume wording without fabricating experience, track application progress, remember cooldown windows, review interview and written-test performance, and build a personal skill profile over time.

The system is designed around user-provided job descriptions and user-owned job-search records. Instead of relying on unstable real-time crawling or unverified online search, CareerPilot-AI focuses on a trustworthy workflow: users bring the JD they care about, and the system helps them evaluate, prepare, track, and improve.

## Highlights

- **JD-Resume Matching**: Analyze a resume against a user-provided job description and generate a structured match report.
- **Trustworthy Resume Optimization**: Improve wording based on real user experience without inventing companies, projects, skills, or metrics.
- **Resume Integrity Guard**: Detect unsupported metrics, exaggerated responsibility claims, inconsistent skills, and fabrication risks.
- **Application Tracker**: Record companies, positions, resume versions, application channels, dates, status changes, and notes.
- **Cooldown Reminder**: Help users avoid forgetting previous applications and remind them when a company may still be in a cooldown period.
- **Interview Review**: Record interview rounds, questions, weak answers, follow-up questions, and generate targeted coaching suggestions.
- **Written-Test Review**: Track problem types, missed knowledge points, and weak areas across companies and test rounds.
- **Skill Profile**: Aggregate JD gaps, resume gaps, interview feedback, and written-test performance into a personal capability map.
- **Privacy-First Design**: Resume and job-search records should remain user-controlled; sensitive data is not persisted unless explicitly required by the user.
- **Evaluation Harness Ready**: Designed to support automated evaluation for parsing, match scoring, integrity checking, prompt-injection defense, and coaching quality.

## Core Workflows

### JD Matching and Resume Optimization

```text
Resume + User-provided JD
-> JD parsing
-> Resume structure extraction
-> Match scoring
-> Gap analysis
-> Trustworthy optimization suggestions
-> Integrity check
-> Structured report
```

### Application Tracking

```text
Target company + position + JD
-> Save application record
-> Track current status
-> Link resume version and analysis report
-> Record outcome
-> Trigger cooldown reminder when needed
```

### Interview and Written-Test Review

```text
Interview or written-test record
-> Capture questions and weak points
-> Tag knowledge areas
-> Generate coaching suggestions
-> Update skill profile
-> Recommend next preparation focus
```

## Product Principles

CareerPilot-AI follows several non-negotiable principles:

- Users provide the JD they want to analyze.
- Optimize expression, not facts.
- Suggest real evidence collection instead of inventing numbers.
- Do not turn "participated in" into "led" unless the user actually led the work.
- Do not add skills, internships, papers, awards, patents, or projects that the user did not provide.
- Treat user-provided resume, JD, and interview notes as sensitive data.
- Use application history to support review and improvement, not to overpromise outcomes.

## Tech Stack

### Frontend

- Vue 3 · Vite · TypeScript
- Vue Router · Pinia · Element Plus · Axios

### Backend

- Python 3.11+ · FastAPI · Pydantic v2
- SQLAlchemy 2.x · SQLite (MVP, PostgreSQL-ready)
- Service layer designed for LLM / Agent drop-in

## Repository Structure

```text
CareerPilot-AI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry + CORS
│   │   ├── core/                # config, database
│   │   ├── models/              # SQLAlchemy models (5 tables)
│   │   ├── schemas/             # Pydantic request / response
│   │   ├── api/v1/              # REST routes (5 modules)
│   │   └── services/            # business logic (rule engine, ready for LLM)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/                 # Axios client + API functions
│       ├── stores/              # Pinia stores (5 modules)
│       ├── components/workspace/# 8 workspace sub-panels
│       └── views/               # WorkspaceView
└── README.md
```

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

API docs auto-served at http://localhost:8002/docs.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend served at http://localhost:5173, expects backend on port 8002.

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analysis/jd-match` | JD-resume matching analysis |
| GET | `/api/v1/analysis/reports` | Historical reports |
| POST | `/api/v1/applications` | Create application record |
| GET | `/api/v1/applications` | List applications |
| PATCH | `/api/v1/applications/{id}/status` | Update application status |
| DELETE | `/api/v1/applications/{id}` | Delete application |
| GET | `/api/v1/applications/{id}/cooldown` | Cooldown check |
| POST | `/api/v1/interviews/reviews` | Create interview review |
| GET | `/api/v1/interviews/reviews` | List interview reviews |
| POST | `/api/v1/written-tests/reviews` | Create written-test review |
| GET | `/api/v1/written-tests/reviews` | List written-test reviews |
| GET | `/api/v1/skill-profile` | Aggregated skill profile |

## Roadmap

- Frontend workspace for JD matching and job-search management.
- Application tracker with status history, resume version linkage, and cooldown reminders.
- Interview review module with question records, answer review, and coaching suggestions.
- Written-test review module with problem tags, weak-point tracking, and skill visualization.
- FastAPI backend with typed request and response models.
- LLM-based analysis workflow with integrity guard and prompt-injection defense.
- Evaluation harness for parser quality, match ranking, coaching quality, hallucination control, and safety checks.

## License

This project is currently under active development. A formal license will be added before public release.