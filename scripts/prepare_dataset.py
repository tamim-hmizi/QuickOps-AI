import json
from app.utils.analyzer import generate_prompt

def convert_to_prompt(project_json):
    prompt = generate_prompt(project_json)
    if "k8s" in prompt:
        output = {
            "recommendation": "k8s",
            "explanation": "Multiple microservices with Docker and Kubernetes configs suggest k8s."
        }
    else:
        output = {
            "recommendation": "vm",
            "explanation": "Single monolithic backend with no container orchestration hints at VM."
        }
    return {"prompt": prompt, "output": json.dumps(output)}

def create_jsonl(input_files, output_file):
    with open(output_file, "w") as out_f:
        for file in input_files:
            with open(file) as f:
                entry = convert_to_prompt(json.load(f))
                out_f.write(json.dumps(entry) + "\n")

create_jsonl(["data/k8s-example.json", "data/vm-example.json"], "data/training.jsonl")
