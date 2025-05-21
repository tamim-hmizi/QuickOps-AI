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
N_CTX = 32768
N_THREADS = 30  
USE_MLOCK = os.getenv("USE_MLOCK", "false").lower() == "true"
MAX_TOKENS = 32768  

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
        # Format frontend info
        frontend_info = f"""
Frontend Repository:
- URL: {project.frontend.repoUrl}
- Metadata: {project.frontend.metadata}
- Files: {[file.get('path', 'N/A') for file in project.frontend.files]}
"""

        # Format backend info
        backend_info = ""
        for idx, backend in enumerate(project.backends):
            backend_info += f"""
Backend #{idx + 1}:
- URL: {backend.repoUrl}
- Metadata: {backend.metadata}
- Files: {[file.get('path', 'N/A') for file in backend.files]}
"""

        # Updated prompt
        prompt = f"""
DONT REGIVE ME THE PROMPT.
You are a senior DevOps engineer.

You will be given a **frontend repository** and an **array of backend repositories**, including their metadata and file listings.

Your task is to analyze this information and recommend whether to deploy the overall project using:
- A **Virtual Machine (VM)**, or
- **Kubernetes (K8s)**.

Take into consideration the presence of:
- Kubernetes manifests (`k8s/`, `.yaml`, `.yml` files),
- Dockerfiles,
- Number of backend services,
- Topics and metadata (e.g., monolith vs microservices).

Use the following logic:
- If there is a **single backend repo with no manifest (e.g., Dockerfile, k8s YAMLs)** → recommend **VM**.
- If there are **multiple backend services**, even without manifests → recommend **Kubernetes**.
- If there's a **single backend repo containing Kubernetes manifests (like `deployment.yaml`, `service.yaml`, etc.)** → recommend **Kubernetes**.

Explain your reasoning clearly in a short paragraph. Just respond with a  recommendation and a concise explanation.

Return your answer as a **JSON object** with the following format:

{{
  "recommendation": "vm" or "kubernetes",
  "explanation": "Detailed reasoning for the chosen deployment method, referencing files, structure, and scalability needs."
}}

Here is the metadata and file structure of the repositories:

{frontend_info}
{backend_info}
"""

        response = llm(prompt, max_tokens=MAX_TOKENS)
        result_text = response["choices"][0]["text"].strip()

        logger.info("Raw LLM Response:\n" + result_text)

        return {"recommendation": result_text}

    except Exception as e:
        logger.exception("Error during LLM analysis.")
        raise HTTPException(status_code=500, detail="LLM inference failed.")



