from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import logging
import re
from dotenv import load_dotenv

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="QuickOps AI Deployment Advisor",
    description="Analyzes GitHub metadata and file structure to recommend VM or Kubernetes deployment.",
    version="1.0.0"
)

generator = None
classifier = None

def load_models():
    global generator, classifier
    from transformers import pipeline

    try:
        generator = pipeline(
            "text-generation",
            model="tiiuae/falcon-rw-1b",  # ✅ public, no token needed
            device=-1
        )
        logger.info("✅ Generator loaded: Falcon-RW-1B")
    except Exception as e:
        logger.error(f"❌ Generator failed: {e}")

    try:
        classifier = pipeline(
            "zero-shot-classification",
            model="typeform/distilbert-base-uncased-mnli",
            device=-1
        )
        logger.info("✅ Classifier loaded")
    except Exception as e:
        logger.error(f"❌ Classifier failed: {e}")

@app.on_event("startup")
def startup_event():
    load_models()

class RepoData(BaseModel):
    repoUrl: str
    metadata: Dict[str, Any]
    files: List[Dict[str, Any]]

class MultiRepoInput(BaseModel):
    frontend: RepoData
    backends: List[RepoData]

@app.get("/health")
def health():
    return {"status": "ok" if generator and classifier else "unhealthy"}

@app.post("/analyze")
async def analyze_deployment(project: MultiRepoInput):
    if generator is None or classifier is None:
        return {"error": "Models not loaded"}

    frontend_info = f"""
Frontend Repository:
- URL: {project.frontend.repoUrl}
- Metadata: {project.frontend.metadata}
- Files: {[file['path'] for file in project.frontend.files[:5]]}
"""

    backend_info = ""
    for idx, backend in enumerate(project.backends):
        backend_info += f"""
Backend #{idx+1} Repository:
- URL: {backend.repoUrl}
- Metadata: {backend.metadata}
- Files: {[file['path'] for file in backend.files[:5]]}
"""

    prompt = f"""
You are a DevOps AI assistant.

Analyze the following project and recommend whether it should be deployed on a VM or on Kubernetes.

Respond only with:
RECOMMENDATION: [VM or KUBERNETES]
EXPLANATION: [your detailed reasoning]

{frontend_info}
{backend_info}
"""

    logger.info("⚙️ Prompt sent to Falcon-RW-1B...")
    raw = generator(prompt, max_new_tokens=200, pad_token_id=50256)[0]["generated_text"]

    recommendation = "UNKNOWN"
    explanation = ""

    for line in raw.splitlines():
        if match := re.match(r"RECOMMENDATION:\s*(.*)", line.strip(), re.IGNORECASE):
            recommendation = match.group(1).strip().upper()
        elif match := re.match(r"EXPLANATION:\s*(.*)", line.strip(), re.IGNORECASE):
            explanation = match.group(1).strip()
        elif explanation:
            explanation += " " + line.strip()

    confidence = classifier(
        explanation,
        candidate_labels=["KUBERNETES", "VM"]
    )
    scores = dict(zip(confidence["labels"], confidence["scores"]))

    return {
        "recommendation": recommendation,
        "explanation": explanation,
        "confidence": scores
    }
