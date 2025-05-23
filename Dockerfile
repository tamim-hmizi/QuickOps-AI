# ========================== BASE ENV ==========================
FROM python:3.10-slim AS python-base

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
  git \
  cmake \
  build-essential \
  libopenblas-dev \
  curl \
  ninja-build \
  && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Clone, patch, and install Axolotl (remove all bitsandbytes imports)
RUN git clone https://github.com/OpenAccess-AI-Collective/axolotl.git /axolotl && \
    find /axolotl -type f -name "*.py" -exec sed -i '/bitsandbytes/d' {} + && \
    pip install /axolotl

# ========================== STAGE 1: TRAIN ==========================
FROM python-base AS builder

COPY . .
ENV PYTHONPATH=/app

RUN python scripts/prepare_dataset.py && \
    axolotl train model/axolotl-config.yaml && \
    axolotl merge model/final-checkpoint --output model/final-checkpoint/merged.gguf

# ========================== STAGE 2: API ==========================
FROM python-base AS runner

COPY --from=builder /app/app ./app
COPY --from=builder /app/model/final-checkpoint ./model/final-checkpoint

ENV PYTHONPATH=/app

EXPOSE 8001
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
