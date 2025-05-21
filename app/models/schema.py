from pydantic import BaseModel
from typing import List

class File(BaseModel):
    path: str
    type: str
    sha: str

class Metadata(BaseModel):
    name: str
    description: str
    language: str
    stars: int
    topics: List[str]

class Repo(BaseModel):
    repoUrl: str
    metadata: Metadata
    files: List[File]

class ProjectInput(BaseModel):
    frontend: Repo
    backends: List[Repo]

class ProjectRecommendation(BaseModel):
    recommendation: str  # "vm" or "k8s"
    explanation: str
