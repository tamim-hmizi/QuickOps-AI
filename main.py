from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from llama_cpp import Llama
import os
import logging
import time

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
FRONTEND:
- URL: {project.frontend.repoUrl}
- Metadata: {project.frontend.metadata}
- Files: {[file['path'] for file in project.frontend.files[:5]]}
"""

    backend_info = ""
    for i, backend in enumerate(project.backends):
        backend_info += f"""
BACKEND #{i + 1}:
- URL: {backend.repoUrl}
- Metadata: {backend.metadata}
- Files: {[file['path'] for file in backend.files[:5]]}
"""

    prompt = f"""
You are a DevOps expert.

You are analyzing a full-stack project with one frontend and multiple backends. Based on the structure, metadata, and file contents, decide whether this entire system should be deployed on a **Virtual Machine (VM)** or on a **Kubernetes (K8s)** cluster.

Do not use technical fluff. Just analyze clearly:
- Are services tightly coupled or independent?
- Is there anything in the metadata or file structure indicating scale, microservices, or distributed load?

Pick only one: VM or Kubernetes. No hybrid answers. No UNKNOWN. Be firm.

### Format:
RECOMMENDATION: [VM or KUBERNETES]  
EXPLANATION: [Short reason, e.g., “The project uses microservices and needs dynamic scaling, so Kubernetes is better.”]

Here is the project data:
{frontend_info}
{backend_info}
"""

    def call_llm_and_parse():
        try:
            response = llm(prompt, max_tokens=2048)
            text = response["choices"][0]["text"].strip()

            recommendation = None
            explanation = ""
            for line in text.splitlines():
                if line.strip().upper().startswith("RECOMMENDATION:"):
                    value = line.split(":", 1)[1].strip().upper()
                    if "KUBERNETES" in value:
                        recommendation = "KUBERNETES"
                    elif "VM" in value:
                        recommendation = "VM"
                elif line.strip().upper().startswith("EXPLANATION:"):
                    explanation = line.split(":", 1)[1].strip()
                elif explanation:
                    explanation += " " + line.strip()
            return recommendation, explanation
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None, ""

    # Try with retries
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        recommendation, explanation = call_llm_and_parse()
        if recommendation in ["VM", "KUBERNETES"]:
            logger.info(f"✅ LLM success on attempt {attempt}")
            return {
                "recommendation": recommendation,
                "explanation": explanation
            }
        logger.warning(f"⚠️ Attempt {attempt} failed. Retrying...")
        time.sleep(1)

    logger.error("❌ LLM failed after multiple attempts. No valid recommendation.")
    return {
        "recommendation": "ERROR",
        "explanation": "Model could not decide after multiple retries. Please refine the metadata or try again later."
    }
