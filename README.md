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

## Frontend Stack

The frontend is built with:

- Vue 3
- Vite
- TypeScript
- Vue Router
- Pinia
- Element Plus
- Axios

## Planned Backend Stack

The backend is planned around:

- Python
- FastAPI
- Pydantic
- PostgreSQL
- Redis
- Agent workflow orchestration
- LLM function calling
- Optional MCP integrations for document parsing, browser-assisted JD capture, and evaluation tools

## Repository Structure

```text
CareerPilot-AI/
|-- frontend/      # Vue 3 frontend application
|-- README.md      # Project introduction
`-- .gitignore     # Git ignore rules
```

## Getting Started

Install frontend dependencies:

```bash
cd frontend
npm install
```

Start the frontend development server:

```bash
npm run dev
```

Build the frontend:

```bash
npm run build
```

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