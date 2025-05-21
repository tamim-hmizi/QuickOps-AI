from llama_cpp import Llama
from app.utils.analyzer import generate_prompt
import json

llm = Llama(model_path="./model/final-checkpoint/merged.gguf", n_ctx=2048)

def get_recommendation(project: dict) -> dict:
    prompt = generate_prompt(project)
    response = llm(prompt, stop=["}"], max_tokens=256)
    text = response["choices"][0]["text"].strip() + "}"
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        return {
            "recommendation": "vm",
            "explanation": f"Parsing error in model output, defaulting to VM: {e}"
        }
