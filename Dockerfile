# ======================= BASE ENVIRONNEMENT PYTHON =======================
FROM python:3.10-slim AS python-base

WORKDIR /app

# Dépendances système nécessaires à tous les stades
RUN apt-get update && apt-get install -y \
  git \
  cmake \
  build-essential \
  libopenblas-dev \
  curl \
  ninja-build \
  && rm -rf /var/lib/apt/lists/*

# Copie requirements.txt et installation des dépendances sans llama-cpp-python
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip
RUN grep -v llama-cpp-python requirements.txt > temp-req.txt && pip install --no-cache-dir -r temp-req.txt

# ✅ Installation propre de llama-cpp-python en CPU-mode
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=OFF"
RUN git clone https://github.com/abetlen/llama-cpp-python.git && \
  cd llama-cpp-python && pip install .

# ======================= STAGE 1 : FINE-TUNING =======================
FROM python-base AS builder

COPY . ./
ENV PYTHONPATH=/app

# Génération du dataset
RUN python scripts/prepare_dataset.py

# Entraînement + fusion GGUF
RUN axolotl train model/axolotl-config.yaml && \
  axolotl merge model/final-checkpoint --output model/final-checkpoint/merged.gguf

# ======================= STAGE 2 : API =======================
FROM python-base AS runner

COPY --from=builder /app/app ./app
COPY --from=builder /app/model/final-checkpoint ./model/final-checkpoint

ENV PYTHONPATH=/app

EXPOSE 8001
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
