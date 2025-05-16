FROM python:3.10-slim

# Crée le dossier de travail
WORKDIR /app

# Copie le code et le fichier requirements
COPY . /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
  libopenblas-dev \
  curl \
  build-essential \
  cmake \
  git \
  ccache \
  && pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt \
  && mkdir -p /app/models \
  && curl -L -o /app/models/zephyr-7b-beta.Q8_0.gguf "https://huggingface.co/TheBloke/zephyr-7B-beta-GGUF/resolve/main/zephyr-7b-beta.Q8_0.gguf?download=true"

# Expose port
EXPOSE 8001

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
