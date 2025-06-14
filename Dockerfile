FROM python:3.11-slim

# Install curl and Ollama dependencies
RUN apt-get update && apt-get install -y curl libssl-dev gnupg && \
    curl -fsSL https://ollama.com/install.sh | sh && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Expose Ollama and FastAPI ports
EXPOSE 8001 11434

WORKDIR /app

# Copy project files
COPY entrypoint.sh /entrypoint.sh
COPY requirements.txt app.py ./

# Setup
RUN chmod +x /entrypoint.sh && pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["/entrypoint.sh"]
