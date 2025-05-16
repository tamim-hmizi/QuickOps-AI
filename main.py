from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv
import os
import logging

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App
app = FastAPI(
    title="QuickOps AI Deployment Advisor",
    description="Analyzes GitHub metadata and file structure to recommend VM or Kubernetes deployment.",
    version="1.0.0"
)

# Global model vars
generator = None
classifier = None

# Load .env (optional for future)
load_dotenv()

# Model loader
def load_models():
    global generator, classifier
    try:
        from transformers import pipeline
        generator = pipeline(
            "text-generation",
            model="gpt2",  # ✅ Light, CPU-compatible model
            device=-1
        )
        logger.info("✅ Generator loaded (gpt2)")
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

# Trigger model load at startup
@app.on_event("startup")
def startup_event():
    load_models()

# Data models
class RepoData(BaseModel):
    repoUrl: str
    metadata: Dict[str, Any]
    files: List[Dict[str, Any]]

class MultiRepoInput(BaseModel):
    frontend: RepoData
    backends: List[RepoData]

# Health check
@app.get("/health")
def health():
    if generator and classifier:
        return {"status": "ok"}
    return {"status": "unhealthy"}

# Analyze endpoint
@app.post("/analyze")
async def analyze_deployment(project: MultiRepoInput):
    if generator is None or classifier is None:
        return {"error": "❌ Models not loaded"}

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

All these repositories are to be deployed together.

Analyze all metadata and file structures, and recommend:
RECOMMENDATION: [VM or KUBERNETES]
EXPLANATION: [Why]

Project:
{frontend_info}
{''.join(backend_blocks)}
"""

    response = generator(prompt, max_new_tokens=150)[0]["generated_text"]

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
