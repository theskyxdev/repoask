<div align="center">

# RepoAsk

### Understand any codebase in minutes, not hours.

RepoAsk turns a GitHub repository into an explorable code intelligence workspace. Ask questions, inspect architecture and dependencies, review security findings, and generate documentation with answers grounded in the repository itself.

[![Open the project](https://img.shields.io/badge/GitHub-theskyxdev%2Frepoask-181717?logo=github)](https://github.com/theskyxdev/repoask)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js-black?logo=next.js)](frontend/)
[![Backend](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi)](backend/)

</div>

---

## Why RepoAsk

Getting oriented in an unfamiliar repository takes time. RepoAsk builds a searchable index of source code and connects the pieces that matter, so developers can move from a broad question to the relevant files and symbols quickly.

Explore a repository through one workspace instead of piecing together separate tools:

- **Evidence-backed chat** answers questions using retrieved code and links claims to source locations.
- **Code search** finds relevant symbols and code snippets across an indexed repository.
- **Architecture explorer** summarizes repository structure and its important components.
- **Dependency graph** visualizes relationships between files and symbols.
- **Security scanner** reports patterns flagged by static analysis.
- **Code review** surfaces automated review findings.
- **Documentation generator** creates repository documentation from indexed code.

## How It Works

1. Add a public GitHub repository in the web app.
2. RepoAsk clones and indexes the project using language-aware parsing and semantic code chunks.
3. Explore the resulting index with search, visualizations, analysis tools, or natural-language questions.
4. Follow citations back to the files and line ranges behind an answer.

On first backend startup, RepoAsk initializes its local database and seeds a small demo repository if the repository list is empty. This gives a fresh local installation something to explore immediately.

## Tech Stack

| Area | Technology |
| --- | --- |
| Web application | Next.js, React, TypeScript, Tailwind CSS |
| API | FastAPI, Python |
| Code understanding | AST parsing, semantic chunking, NetworkX |
| Retrieval | ChromaDB, embeddings |
| Optional language model | Google Gemini |

## Run Locally

### Requirements

- Python 3.10 or later
- Node.js and npm
- Git

### 1. Start the backend

From the repository root, create and activate a virtual environment, then install the backend requirements:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API health check is available at [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health), and interactive API documentation is at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 2. Start the frontend

Open a second terminal at the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

The frontend defaults to `http://127.0.0.1:8000/api/v1`. To use a different API URL, create `frontend/.env.local` and set:

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
```

Restart the frontend after changing environment variables.

## Gemini Configuration

The core code exploration and static analysis workflow can run without a Gemini key. Gemini-backed responses or documentation may require a key, depending on the selected feature. Add your key to `backend/.env`:

```dotenv
GEMINI_API_KEY=your_key_here
```

You can also provide a Gemini key in the app's settings. Never commit `.env` or `.env.local` files; only the example configuration belongs in source control.

## Project Layout

```text
.
├── assets/                 # Shared project assets
├── backend/
│   ├── app/
│   │   ├── parser/          # Language detection, AST parsing, chunking, dependencies
│   │   ├── routers/         # FastAPI endpoints
│   │   ├── services/        # Indexing, chat, review, security, documentation
│   │   └── vectorstore/     # Retrieval storage
│   └── requirements.txt
└── frontend/
    ├── src/app/             # Next.js application routes and global styles
    ├── src/components/      # Workspace and feature interfaces
    ├── src/lib/             # API client and utilities
    └── package.json
```

Runtime databases, vector indexes, and cloned repositories are stored locally under `backend/data/` and are intentionally excluded from Git.

## Development Checks

Run the frontend linter:

```powershell
cd frontend
npm run lint
```

Create a production frontend build:

```powershell
cd frontend
npm run build
```

## Current Scope

RepoAsk is designed for local development and analysis of public GitHub repositories. The API includes a basic in-memory request rate limit and security response headers; these are useful development safeguards, not a substitute for production deployment controls. Configure secrets, allowed origins, persistence, resource limits, and authentication appropriately before exposing an instance publicly.

## Contributing

Contributions are welcome. For a change, include a concise description of the behavior, the steps used to verify it, and any configuration changes needed to run it locally.

## License

No license is currently included in this repository. Contact the repository owner for permission before redistributing or reusing the project.
