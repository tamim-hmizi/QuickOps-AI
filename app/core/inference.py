from llama_cpp import Llama
from app.utils.analyzer import generate_prompt
import json

# Load GGUF CPU-only model
llm = Llama(
    model_path="./model/final-checkpoint/merged.gguf",
    n_ctx=2048,
    n_threads=4  # adjust based on your CPU
)

def get_recommendation(project: dict) -> dict:
    prompt = generate_prompt(project)
    full_prompt = f"{prompt}\nReturn a JSON like: {{\"recommendation\": \"k8s\", \"explanation\": \"...\"}}"
    
    response = llm(full_prompt, stop=["}"], max_tokens=256)
    text = response["choices"][0]["text"].strip() + "}"
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        return {
            "recommendation": "vm",
            "explanation": f"Parsing error in model output, defaulting to VM: {e}"
        }
