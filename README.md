<div align="center">
  <img src="frontend/LOGO.png" alt="CareerPilot-AI Logo" width="140" />
  <h1>CareerPilot-AI</h1>
  <p><strong>An intelligent JD-Resume matching and career application optimization system.</strong></p>
</div>

---

CareerPilot-AI is an intelligent job application optimization system built around JD-Resume matching. It helps users analyze how well their resume fits a target job description, identify missing evidence or weak expressions, and generate trustworthy improvement suggestions without fabricating experience.

The system is designed for general job-search scenarios, including software engineering, AI engineering, product, testing, operations, data analysis, and other roles. For users without a specific job description, CareerPilot-AI can also use a JD knowledge base to summarize common role requirements and recommend suitable job opportunities.

## Highlights

- **JD-Resume Matching**: Analyze a resume against a specific job description and generate a structured match report.
- **Role-Direction Matching**: Support users who only know their target direction by using a JD knowledge base to build a general role profile.
- **Trustworthy Resume Optimization**: Improve wording based on real user experience instead of inventing companies, projects, skills, or metrics.
- **Resume Integrity Guard**: Detect unsupported metrics, exaggerated responsibility claims, inconsistent skills, and potential fabrication risks.
- **JD Knowledge Base**: Store and structure job descriptions for retrieval, aggregation, role profiling, and recommendation scenarios.
- **Prompt Injection Awareness**: Treat resumes and job descriptions as untrusted input and prevent user-provided text from overriding system rules.
- **Privacy-First Design**: Resume content is not persisted by default; JD data can be anonymized and added to the knowledge base only with explicit user permission.
- **Evaluation Harness Ready**: Designed to support automated evaluation for JD parsing, match scoring, recommendation quality, integrity checking, and prompt injection defense.

## Core Workflows

### Specific JD Matching

```text
Resume + Job Description
-> JD parsing
-> Resume structure extraction
-> Match scoring
-> Gap analysis
-> Optimization suggestions
-> Integrity check
-> Structured report
```

This workflow is used when a user already has a target company or job description.

### Role-Direction Matching

```text
Resume + Target Direction
-> JD knowledge base retrieval
-> Role profile generation
-> Resume-role matching
-> Capability gap analysis
-> Job recommendation
-> Optimization suggestions
```

This workflow is used when a user only knows the type of role they want, such as AI Engineer, Agent Developer, Backend Engineer, Product Manager, Testing Engineer, or Operations Specialist.

## Product Principles

CareerPilot-AI follows several non-negotiable principles:

- Optimize expression, not facts.
- Suggest real evidence collection instead of inventing numbers.
- Do not turn "participated in" into "led" unless the user actually led the work.
- Do not add skills, internships, papers, awards, patents, or projects that the user did not provide.
- Flag uncertain, unsupported, or risky statements instead of silently polishing them.
- Keep resume data private by default.

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
- pgvector or another vector retrieval solution
- Agent workflow orchestration
- LLM function calling
- Optional MCP integrations for external data sources and tools

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

- Frontend workspace for resume and JD input.
- Structured match report with match overview, JD parsing, resume summary, gap analysis, optimization suggestions, integrity checks, and job recommendations.
- FastAPI backend with typed request and response models.
- JD knowledge base with structured parsing, deduplication, quality scoring, and vector retrieval.
- LLM-based analysis workflow with integrity guard and prompt injection defense.
- Evaluation harness for parser quality, match ranking, recommendation relevance, hallucination control, and safety checks.

## License

This project is currently under active development. A formal license will be added before public release.