# ============================
# STAGE 1: TRAINING + MERGE
# ============================
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
  libopenblas-dev \
  curl \
  build-essential \
  cmake \
  git \
  ccache \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY ./data ./data
COPY ./model ./model
COPY ./scripts ./scripts

ENV PYTHONPATH=/app

# Prepare dataset
RUN python scripts/prepare_dataset.py

# Fine-tune + merge
RUN axolotl train model/axolotl-config.yaml && \
  axolotl merge model/final-checkpoint --output model/final-checkpoint/merged.gguf

# ============================
# STAGE 2: API ONLY
# ============================
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libopenblas-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=builder /app/app ./app
COPY --from=builder /app/model/final-checkpoint ./model/final-checkpoint

ENV PYTHONPATH=/app

EXPOSE 8001
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
