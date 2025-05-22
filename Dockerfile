# ============================ STAGE 1: TRAINING ============================
FROM python:3.10-slim AS builder

WORKDIR /app

# Dépendances système pour le build et llama-cpp-python
RUN apt-get update && apt-get install -y \
  git \
  cmake \
  build-essential \
  libopenblas-dev \
  curl \
  ninja-build \
  && rm -rf /var/lib/apt/lists/*

# Installer pip & dépendances Python (sans llama-cpp-python)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip
RUN grep -v llama-cpp-python requirements.txt > temp-req.txt && pip install --no-cache-dir -r temp-req.txt

# Installer llama-cpp-python CPU-only manuellement
RUN git clone https://github.com/abetlen/llama-cpp-python.git && \
  cd llama-cpp-python && \
  pip install --no-cache-dir . --config-settings=--build-option=--use-cpu

# Copier tout le projet
COPY . ./
ENV PYTHONPATH=/app

# Préparation du dataset
RUN python scripts/prepare_dataset.py

# Fine-tuning + fusion GGUF
RUN axolotl train model/axolotl-config.yaml && \
  axolotl merge model/final-checkpoint --output model/final-checkpoint/merged.gguf

# ============================ STAGE 2: API ============================
FROM python:3.10-slim AS runner

WORKDIR /app

# ✅ Installer git (correction de l’erreur) + autres dépendances
RUN apt-get update && apt-get install -y \
  git \
  libopenblas-dev \
  cmake \
  ninja-build \
  && rm -rf /var/lib/apt/lists/*

# Installer pip & dépendances Python (sans llama-cpp-python)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip
RUN grep -v llama-cpp-python requirements.txt > temp-req.txt && pip install --no-cache-dir -r temp-req.txt

# Installer llama-cpp-python CPU-only manuellement
RUN git clone https://github.com/abetlen/llama-cpp-python.git && \
  cd llama-cpp-python && \
  pip install --no-cache-dir . --config-settings=--build-option=--use-cpu

# Copier code et modèle entraîné depuis le builder
COPY --from=builder /app/app ./app
COPY --from=builder /app/model/final-checkpoint ./model/final-checkpoint

ENV PYTHONPATH=/app

EXPOSE 8001
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
