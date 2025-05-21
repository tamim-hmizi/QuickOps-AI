def flatten_topics(repo):
    return " ".join(repo["metadata"].get("topics", []))

def generate_prompt(project):
    prompt = f"Frontend:\n"
    prompt += f"- Language: {project['frontend']['metadata']['language']}\n"
    prompt += f"- Topics: {project['frontend']['metadata']['topics']}\n"
    prompt += f"- Files: {project['frontend']['files']}\n\n"

    for backend in project['backends']:
        prompt += f"Backend: {backend['name']}\n"
        prompt += f"- Language: {backend['metadata']['language']}\n"
        prompt += f"- Topics: {backend['metadata']['topics']}\n"
        prompt += f"- Files: {backend['files']}\n\n"

    prompt += "Based on this architecture, should this project be deployed on Kubernetes or a Virtual Machine?\n"
    return prompt

