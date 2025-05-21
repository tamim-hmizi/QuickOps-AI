from fastapi import FastAPI
from app.models.schema import ProjectInput, ProjectRecommendation
from app.core.inference import get_recommendation

app = FastAPI()

@app.post("/recommend", response_model=ProjectRecommendation)
def recommend_infrastructure(project: ProjectInput):
    return get_recommendation(project.dict())

@app.get("/health")
def health_check():
    return {"status": "ok"}
