from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from llama_cpp import Llama
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = "models/zephyr-7b-beta.Q8_0.gguf"

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=4,
    use_mlock=True
)

app = FastAPI()


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
- Files: {[file['path'] for file in project.frontend.files[:5]]}
"""

    backend_info = ""
    for i, backend in enumerate(project.backends):
        backend_info += f"""
Backend #{i + 1} Repository:
- URL: {backend.repoUrl}
- Metadata: {backend.metadata}
- Files: {[file['path'] for file in backend.files[:5]]}
"""

    prompt = f"""
You are a DevOps expert.

I have one frontend repository and one or more backend repositories. Your task is to analyze their structure, scale, metadata, and file types to decide whether this **entire application** (frontend and all backends) should be deployed using a **Virtual Machine (VM)** or a **Kubernetes (K8s) cluster**.

You must consider:
- the number and separation of services,
- deployment and scalability needs,
- architectural style (monolithic vs microservices),
- metadata indicators,
- and infrastructure complexity.

⚠️ You must choose **only one** between VM or Kubernetes for the **entire project**. No hybrid or partial answers. No UNKNOWNs. No hesitation.

Respond exactly in the following format:

RECOMMENDATION: [VM or KUBERNETES]  
EXPLANATION: [a clear, justified explanation based on the analysis]

Here is the project context:

{frontend_info}
{backend_info}
"""

    def call_llm_and_parse():
        result = llm(prompt, max_tokens=30000)
        text = result["choices"][0]["text"].strip()

        recommendation = None
        explanation = ""
        for line in text.splitlines():
            if line.strip().upper().startswith("RECOMMENDATION:"):
                value = line.split(":", 1)[1].strip().upper()
                if "VM" in value:
                    recommendation = "VM"
                elif "KUBERNETES" in value:
                    recommendation = "KUBERNETES"
            elif line.strip().upper().startswith("EXPLANATION:"):
                explanation = line.split(":", 1)[1].strip()
            elif explanation:
                explanation += " " + line.strip()
        return recommendation, explanation

    # First try
    recommendation, explanation = call_llm_and_parse()

    # Retry once if response is invalid
    if recommendation not in ["VM", "KUBERNETES"]:
        logger.warning("⚠️ LLM did not return a clear recommendation. Retrying once...")
        recommendation, explanation = call_llm_and_parse()

    # Raise error if still not valid
    if recommendation not in ["VM", "KUBERNETES"]:
        raise ValueError("❌ LLM failed to provide a clear RECOMMENDATION. Please refine the prompt or check the model output.")

    return {
        "recommendation": recommendation,
        "explanation": explanation
    }
