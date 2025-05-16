from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from transformers import pipeline
from dotenv import load_dotenv
import os
import logging

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env
load_dotenv()
hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
if not hf_token:
    raise RuntimeError("❌ HUGGINGFACE_HUB_TOKEN not found in .env")

# App init
app = FastAPI(
    title="QuickOps AI Deployment Advisor",
    description="Analyzes GitHub metadata and file structure to recommend VM or Kubernetes deployment.",
    version="1.0.0"
)

# Load models safely
generator = None
classifier = None

try:
    generator = pipeline(
        "text-generation",
        model="mistralai/Mistral-7B-Instruct-v0.1",
        use_auth_token=hf_token,
        device=-1  # Force CPU in Docker
    )
    logger.info("✅ Generator loaded")
except Exception as e:
    logger.error(f"❌ Failed to load generator: {e}")

try:
    classifier = pipeline(
        "zero-shot-classification",
        model="typeform/distilbert-base-uncased-mnli",
        device=-1
    )
    logger.info("✅ Classifier loaded")
except Exception as e:
    logger.error(f"❌ Failed to load classifier: {e}")

# Schemas
class RepoData(BaseModel):
    repoUrl: str
    metadata: Dict[str, Any]
    files: List[Dict[str, Any]]

class MultiRepoInput(BaseModel):
    frontend: RepoData
    backends: List[RepoData]

# Health endpoint
@app.get("/health")
def health():
    if generator is None or classifier is None:
        return {"status": "unhealthy"}
    return {"status": "ok"}

# Main analyze endpoint
@app.post("/analyze")
async def analyze(project: MultiRepoInput):
    if generator is None or classifier is None:
        return {"error": "❌ Model not loaded"}

    frontend_info = f"""
Frontend Repository:
- URL: {project.frontend.repoUrl}
- Metadata: {project.frontend.metadata}
- Files (sample): {[file['path'] for file in project.frontend.files[:20]]}
"""

    backend_blocks = [
        f"""
Backend #{i+1} Repository:
- URL: {b.repoUrl}
- Metadata: {b.metadata}
- Files (sample): {[f['path'] for f in b.files[:20]]}
""" for i, b in enumerate(project.backends)
    ]

    prompt = f"""
You are a DevOps AI assistant.

You are given a full-stack project composed of:
- 1 frontend repository
- 1 or more backend repositories

All these repositories are to be deployed together.

Analyze all metadata and file structures, then recommend:
RECOMMENDATION: [VM or KUBERNETES]
EXPLANATION: [Why]

Project:
{frontend_info}
{''.join(backend_blocks)}
"""

    result = generator(prompt, max_new_tokens=300)[0]["generated_text"]

    # Parse output
    lines = result.splitlines()
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

    confidence_result = classifier(explanation, candidate_labels=["KUBERNETES", "VM"])
    scores = dict(zip(confidence_result["labels"], confidence_result["scores"]))

    return {
        "recommendation": recommendation,
        "explanation": explanation,
        "confidence": scores
    }
