from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from llama_cpp import Llama
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("devops-analyzer")

MODEL_PATH = "models/zephyr-7b-beta.Q8_0.gguf"
N_CTX = 8192  
N_THREADS = 30  
USE_MLOCK = os.getenv("USE_MLOCK", "false").lower() == "true"
MAX_TOKENS = 8192  

try:
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=N_CTX,
        n_threads=N_THREADS,
        use_mlock=USE_MLOCK,
        verbose=False
    )
    logger.info("LLM model loaded successfully.")
except Exception as e:
    logger.error(f"Error loading LLM model: {e}")
    raise RuntimeError("Failed to initialize LLM. Verify MODEL_PATH and system resources.")

app = FastAPI(title="DevOps Deployment Analyzer")

@app.on_event("startup")
async def startup_event():
    logger.info("API started. LLM ready for inference.")

class RepoData(BaseModel):
    repoUrl: str
    metadata: Dict[str, Any]
    files: List[Dict[str, Any]]

class MultiRepoInput(BaseModel):
    frontend: RepoData
    backends: List[RepoData]

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "LLM is operational."}

@app.post("/analyze")
async def analyze_deployment(project: MultiRepoInput):
    try:
        frontend_info = f"""
FRONTEND:
- URL: {project.frontend.repoUrl}
- Metadata: {project.frontend.metadata}
- Files: {[file.get('path', 'N/A') for file in project.frontend.files]}
"""

        backend_info = ""
        for idx, backend in enumerate(project.backends):
            backend_info += f"""
BACKEND #{idx + 1}:
- URL: {backend.repoUrl}
- Metadata: {backend.metadata}
- Files: {[file.get('path', 'N/A') for file in backend.files]}
"""

        prompt = f"""
You are a senior DevOps engineer.

Analyze the full-stack project described below, consisting of a frontend and multiple backends. Based on the files and metadata provided, recommend if this should be deployed using a Virtual Machine (VM) or a Kubernetes (K8s) cluster.

Rules:
- If the project is a monolith, use VM.
- If no Kubernetes-related files are found, use VM.
- If multiple independent backends are present, use Kubernetes.
- Choose only ONE: VM or KUBERNETES.

Format your output as:
RECOMMENDATION: [VM or KUBERNETES]  
EXPLANATION: [Concise reason here.]

PROJECT DATA:
{frontend_info}
{backend_info}
"""

        response = llm(prompt, max_tokens=MAX_TOKENS)
        result_text = response["choices"][0]["text"].strip()

        recommendation = None
        explanation = ""
        for line in result_text.splitlines():
            line_clean = line.strip()
            if line_clean.upper().startswith("RECOMMENDATION:"):
                recommendation = line_clean.split(":", 1)[1].strip().upper()
            elif line_clean.upper().startswith("EXPLANATION:"):
                explanation = line_clean.split(":", 1)[1].strip()
            elif explanation:
                explanation += " " + line_clean

        if recommendation not in {"VM", "KUBERNETES"}:
            logger.warning("No valid recommendation found; defaulting to VM.")
            recommendation = "VM"
            explanation = "Defaulted to VM as no clear recommendation was provided."

        logger.info(f"Deployment recommendation: {recommendation}")
        return {
            "recommendation": recommendation,
            "explanation": explanation
        }

    except Exception as e:
        logger.exception("Error during LLM analysis.")
        raise HTTPException(status_code=500, detail="LLM inference failed.")
