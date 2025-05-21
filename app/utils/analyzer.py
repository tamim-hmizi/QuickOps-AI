def flatten_topics(repo):
    return " ".join(repo["metadata"].get("topics", []))

def generate_prompt(project: dict) -> str:
    prompt = "Given the project structure, recommend either VM or Kubernetes:\n\n"

    prompt += f"Frontend Repo:\n"
    prompt += f"- Language: {project['frontend']['metadata']['language']}\n"
    prompt += f"- Topics: {flatten_topics(project['frontend'])}\n"
    prompt += f"- Files: {[f['path'] for f in project['frontend']['files']]}\n\n"

    for i, backend in enumerate(project['backends']):
        prompt += f"Backend {i+1}:\n"
        prompt += f"- Language: {backend['metadata']['language']}\n"
        prompt += f"- Topics: {flatten_topics(backend)}\n"
        prompt += f"- Files: {[f['path'] for f in backend['files']]}\n\n"

    prompt += 'Output in this format:\n{ "recommendation": "vm" or "k8s", "explanation": "short reason" }'
    return prompt
