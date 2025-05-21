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
        frontend_info = f"""
Frontend Repo:
- Name: {project.frontend.metadata.get('name')}
- Language: {project.frontend.metadata.get('language')}
- Files: {[file.get('path', 'N/A') for file in project.frontend.files]}
"""

        backend_info = ""
        for idx, backend in enumerate(project.backends):
            backend_info += f"""
Backend #{idx + 1}:
- Name: {backend.metadata.get('name')}
- Language: {backend.metadata.get('language')}
- Files: {[file.get('path', 'N/A') for file in backend.files]}
"""

        prompt = f"""
You are a senior DevOps engineer.

Your task is to analyze the following frontend and backends and determine whether the project should be deployed using a Virtual Machine (VM) or Kubernetes (K8s).

Rules:
- Use **VM** for monolithic or single backend applications.
- Use **KUBERNETES** if there are multiple independent services or microservices.
- Choose only one: either "VM" or "KUBERNETES".
- Return ONLY JSON like this: {{ "recommendation": "VM" or "KUBERNETES", "explanation": "one-line explanation" }}

Do not repeat the prompt or include anything else. Just return the JSON.

{frontend_info}
{backend_info}
"""

        response = llm(prompt, max_tokens=MAX_TOKENS)
        result_text = response["choices"][0]["text"].strip()

        logger.info("Raw LLM Response:\n" + result_text)

        # Clean up and parse LLM's response as JSON
        import json
        try:
            parsed = json.loads(result_text)
            return parsed
        except json.JSONDecodeError:
            logger.error("Invalid JSON returned by LLM.")
            raise HTTPException(status_code=500, detail="LLM returned invalid JSON.")

    except Exception as e:
        logger.exception("Error during LLM analysis.")
        raise HTTPException(status_code=500, detail="LLM inference failed.")


