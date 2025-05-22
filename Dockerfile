# ============ STAGE 1: TRAIN + MERGE ============
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
  libopenblas-dev \
  build-essential \
  cmake \
  git \
  curl && \
  rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt

COPY . ./
ENV PYTHONPATH=/app

# Préparation dataset
RUN python scripts/prepare_dataset.py

# Entraînement + fusion modèle
RUN axolotl train model/axolotl-config.yaml && \
  axolotl merge model/final-checkpoint --output model/final-checkpoint/merged.gguf

# ============ STAGE 2: INFERENCE API ============
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libopenblas-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=builder /app/app ./app
COPY --from=builder /app/model/final-checkpoint ./model/final-checkpoint

ENV PYTHONPATH=/app

EXPOSE 8001
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
