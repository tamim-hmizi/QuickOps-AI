from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from llama_cpp import Llama
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the LLaMA model
MODEL_PATH = "models/zephyr-7b-beta.Q8_0.gguf"

# Load the model
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=4,
    use_mlock=True
)

# Initialize FastAPI
app = FastAPI()

# Define input schemas
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
    # Format frontend data
    frontend_info = f"""
FRONTEND:
- URL: {project.frontend.repoUrl}
- Metadata: {project.frontend.metadata}
- Files: {[file['path'] for file in project.frontend.files[:5]]}
"""

    # Format backend data
    backend_info = ""
    for i, backend in enumerate(project.backends):
        backend_info += f"""
BACKEND #{i + 1}:
- URL: {backend.repoUrl}
- Metadata: {backend.metadata}
- Files: {[file['path'] for file in backend.files[:5]]}
"""

    # Final prompt for LLM
    prompt = f"""
You are a DevOps expert.

You are analyzing a full-stack project with one frontend and one or more backends. Your job is to decide whether this project should be deployed on a **Virtual Machine (VM)** or on a **Kubernetes (K8s)** cluster.

Use these deployment rules:
- If the project is a **monolith**, deploy it on a **VM**.
- If **no Kubernetes-related files** (like Dockerfiles, Helm charts, manifests) are found, deploy to a **VM**.
- If there are **multiple independent backends**, recommend **Kubernetes**.
- Choose only ONE deployment type: either **VM** or **KUBERNETES**. No hybrid answers. No "Unknown".

Output format:
RECOMMENDATION: [VM or KUBERNETES]  
EXPLANATION: [Short reason, e.g., “The project uses microservices and needs dynamic scaling, so Kubernetes is better.”]

Here is the project data:
{frontend_info}
{backend_info}
"""

    # Call the LLM and parse response
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

    # Retry until success
    attempt = 0
    while True:
        attempt += 1
        recommendation, explanation = call_llm_and_parse()
        if recommendation in ["VM", "KUBERNETES"]:
            logger.info(f"✅ LLM success on attempt {attempt}")
            return {
                "recommendation": recommendation,
                "explanation": explanation
            }
        logger.warning(f"⚠️ Attempt {attempt} failed. Retrying in 1 second...")
        time.sleep(1)
