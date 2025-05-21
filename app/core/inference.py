from llama_cpp import Llama
from app.utils.analyzer import generate_prompt
import json

llm = Llama(model_path="./model/final-checkpoint/merged.gguf", n_ctx=2048)

def get_recommendation(project: dict) -> dict:
    prompt = generate_prompt(project)
    response = llm(prompt, stop=["}"], max_tokens=256)
    text = response["choices"][0]["text"] + "}"
    return json.loads(text.strip())
