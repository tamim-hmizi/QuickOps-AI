import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

GITHUB_API = "https://api.github.com/repos"

class Input(BaseModel):
    frontend: str
    backends: List[str]
    token: str  # GitHub PAT

class Output(BaseModel):
    recommendation: str
    reasoning: str

app = FastAPI()

def fetch_metadata(repo_url, token: str):
    parts = repo_url.rstrip('/').split('/')
    owner, repo = parts[-2], parts[-1]
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    # Repo metadata
    resp = requests.get(f"{GITHUB_API}/{owner}/{repo}", headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"GitHub fetch failed: {resp.text}")
    data = resp.json()

    # Check for Dockerfile
    docker_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/Dockerfile"
    docker_resp = requests.get(docker_url, headers=headers)
    has_dockerfile = docker_resp.status_code == 200

    return {
        "name": data["full_name"],
        "stars": data["stargazers_count"],
        "language": data.get("language"),
        "forks": data["forks_count"],
        "has_dockerfile": has_dockerfile,
        "topics": data.get("topics", [])
    }

def build_prompt(metadata_list):
    prompt = (
        "You are an expert DevOps assistant.\n"
        "Based on the following GitHub repository metadata for a full application stack (1 frontend and multiple backends),\n"
        "recommend ONE deployment option: 'Kubernetes' or 'VM'. Justify clearly.\n\n"
    )
    for i, meta in enumerate(metadata_list):
        prompt += f"Repo {i+1}: {meta['name']}\n"
        prompt += f"  Stars: {meta['stars']}\n"
        prompt += f"  Language: {meta['language']}\n"
        prompt += f"  Forks: {meta['forks']}\n"
        prompt += f"  Has Dockerfile: {meta['has_dockerfile']}\n"
        prompt += f"  Topics: {', '.join(meta['topics'])}\n\n"
    prompt += "Answer in this format:\nRecommendation: <Kubernetes or VM>\nReasoning: <why>\n"
    return prompt

def ask_llm(prompt):
    payload = {"model": "llama3.2", "prompt": prompt}
    resp = requests.post("http://localhost:11434/api/generate", json=payload)
    resp.raise_for_status()
    return resp.json()["response"]

@app.post("/suggest", response_model=Output)
def suggest(input: Input):
    all_urls = [input.frontend] + input.backends
    metadata = [fetch_metadata(url, input.token) for url in all_urls]
    prompt = build_prompt(metadata)
    llm_reply = ask_llm(prompt)

    # Parse LLM output
    recommendation = ""
    reasoning = ""
    for line in llm_reply.splitlines():
        if line.lower().startswith("recommendation:"):
            recommendation = line.split(":", 1)[1].strip()
        elif line.lower().startswith("reasoning:"):
            reasoning = line.split(":", 1)[1].strip()
    return Output(recommendation=recommendation, reasoning=reasoning)
