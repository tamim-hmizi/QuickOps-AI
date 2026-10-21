# QuickOps AI

QuickOps AI is the recommendation service of QuickOps, a DevOps-as-a-Service platform. Given the GitHub repositories of an application (one frontend and one or more backends), it collects repository metadata, asks a locally hosted LLM (Llama 3.2 through Ollama) to choose between a virtual machine and a Kubernetes deployment, and returns the recommendation with its reasoning.

## Features

- `POST /suggest` endpoint taking `frontend` (URL), `backends` (list of URLs) and `token` (GitHub personal access token)
- Fetches metadata from the GitHub API for each repository: full name, stars, forks, language, topics, and whether a `Dockerfile` exists on `main`
- Builds a DevOps-expert prompt and streams the answer from Ollama (`llama3.2` by default)
- Parses the answer into `recommendation` (`Kubernetes` or `VM`) and `reasoning`, with a keyword fallback
- CORS enabled for the web console
- Small, non-root API image; Ollama runs as its own container from the official image, wired up in `compose.yaml`

## Tech stack

Python 3.11, FastAPI, Pydantic, Uvicorn, Requests, Ollama with Llama 3.2, Docker.

## Architecture

The frontend calls `/suggest` from the project detail page and saves the result on the project through the backend, which uses the chosen target (VM or Kubernetes) when deploying.

## Related repositories

| Repository | Role |
|---|---|
| [QuickOps-Frontend](https://github.com/tamim-hmizi/QuickOps-Frontend) | React web console |
| [QuickOps-Backend](https://github.com/tamim-hmizi/QuickOps-Backend) | Express/MongoDB API and deployment orchestrator |
| [QuickOps-AI](https://github.com/tamim-hmizi/QuickOps-AI) | FastAPI + LLM deployment recommender |
| [QuickOps-IAC](https://github.com/tamim-hmizi/QuickOps-IAC) | Terraform for the QuickOps platform VM |
| [QuickOps-CAC](https://github.com/tamim-hmizi/QuickOps-CAC) | Ansible configuration of the DevOps toolchain |

## Getting started

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) with the `llama3.2` model, or Docker

### Run locally

```bash
pip install -r requirements.txt
ollama serve &
ollama pull llama3.2
uvicorn app:app --host 0.0.0.0 --port 8001
```

### Run with Docker Compose

```bash
docker compose up --build
```

This starts Ollama, pulls `llama3.2` into a named volume on the first run, then starts the API on port 8001.

### Example request

```bash
curl -X POST http://localhost:8001/suggest \
  -H "Content-Type: application/json" \
  -d '{"frontend":"https://github.com/<owner>/<frontend>","backends":["https://github.com/<owner>/<backend>"],"token":"<GITHUB_TOKEN>"}'
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Base URL of the Ollama server |
| `OLLAMA_MODEL` | `llama3.2` | Model used for the recommendation |
| `CORS_ORIGINS` | `*` | Comma-separated origins allowed to call the API |

### Tests

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest
```

The tests stub GitHub and Ollama, so they need neither network access nor a model.

## Project context

RFC final year project, 2025, by Tamim Hmizi: https://tamim-hmizi.github.io/Portfolio/
