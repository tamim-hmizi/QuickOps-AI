from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from transformers import pipeline

app = FastAPI()

generator = pipeline("text-generation", model="tiiuae/falcon-rw-1b")
classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")

class RepoData(BaseModel):
    repoUrl: str
    metadata: Dict[str, Any]
    files: List[Dict[str, Any]]

class MultiRepoInput(BaseModel):
    frontend: RepoData
    backends: List[RepoData]

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/analyze")
async def analyze_deployment(project: MultiRepoInput):
    frontend_info = f"""
Frontend Repository:
- URL: {project.frontend.repoUrl}
- Metadata: {project.frontend.metadata}
- Files (sample): {[file['path'] for file in project.frontend.files[:20]]}
"""

    backend_blocks = []
    for idx, backend in enumerate(project.backends):
        backend_block = f"""
Backend #{idx + 1} Repository:
- URL: {backend.repoUrl}
- Metadata: {backend.metadata}
- Files (sample): {[file['path'] for file in backend.files[:20]]}
"""
        backend_blocks.append(backend_block)

    prompt = f"""
You are a DevOps AI assistant.

You are given a full-stack project composed of:
- 1 frontend repository
- 1 or more backend repositories

All these repositories are to be deployed **together on the same infrastructure**.

Analyze all the provided metadata and file structures and recommend whether this project
should be deployed on a **Virtual Machine (VM)** or on a **Kubernetes cluster**.

Respond in this format:
RECOMMENDATION: [VM or KUBERNETES]
EXPLANATION: [Your explanation of the decision.]

Here is the project data:
{frontend_info}
{''.join(backend_blocks)}
"""

    response = generator(prompt, max_new_tokens=300)[0]['generated_text']

    lines = response.splitlines()
    recommendation = "UNKNOWN"
    explanation = ""

    for line in lines:
        if line.strip().upper().startswith("RECOMMENDATION:"):
            if "KUBERNETES" in line.upper():
                recommendation = "KUBERNETES"
            elif "VM" in line.upper():
                recommendation = "VM"
        elif line.strip().upper().startswith("EXPLANATION:"):
            explanation = line.partition(":")[2].strip()
        elif explanation:
            explanation += " " + line.strip()

    confidence_result = classifier(
        explanation,
        candidate_labels=["KUBERNETES", "VM"]
    )

    confidence_scores = dict(zip(confidence_result["labels"], confidence_result["scores"]))

    return {
        "recommendation": recommendation,
        "explanation": explanation,
        "confidence": confidence_scores
    }
