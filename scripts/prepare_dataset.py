import json
from app.utils.analyzer import generate_prompt

def convert_to_prompt(project_json):
    prompt = generate_prompt(project_json)
    if any("k8s" in topic or "kubernetes" in topic for backend in project_json["backends"] for topic in backend["metadata"]["topics"]):
        output = {
            "recommendation": "k8s",
            "explanation": "Multiple microservices with container orchestration hint at Kubernetes."
        }
    else:
        output = {
            "recommendation": "vm",
            "explanation": "Monolithic architecture without orchestration favors VM deployment."
        }
    return {
        "instruction": "Based on the software architecture, decide the deployment.",
        "input": prompt,
        "output": json.dumps(output)
    }

def create_jsonl(input_files, output_file):
    with open(output_file, "w") as out_f:
        for file in input_files:
            with open(file) as f:
                entry = convert_to_prompt(json.load(f))
                out_f.write(json.dumps(entry) + "\n")

create_jsonl(["data/k8s-example.json", "data/vm-example.json"], "data/training.jsonl")
