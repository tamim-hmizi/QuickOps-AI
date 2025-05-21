from pydantic import BaseModel
from typing import List, Optional

class Metadata(BaseModel):
    name: str
    description: str
    language: str
    stars: int
    topics: List[str]

class Repo(BaseModel):
    repoUrl: Optional[str] = None
    metadata: Metadata
    files: List[str]

class ProjectInput(BaseModel):
    frontend: Repo
    backends: List[Repo]

class ProjectRecommendation(BaseModel):
    recommendation: str 
    explanation: str
