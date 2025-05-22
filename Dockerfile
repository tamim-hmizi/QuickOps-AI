# ========================== BASE ENV ==========================
FROM python:3.10-slim AS python-base

WORKDIR /app

RUN apt-get update && apt-get install -y \
  git \
  cmake \
  build-essential \
  libopenblas-dev \
  curl \
  ninja-build \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip
RUN grep -v llama-cpp-python requirements.txt > temp-req.txt && pip install --no-cache-dir -r temp-req.txt

# ✅ Installer Axolotl sans extras (évite bitsandbytes)
RUN pip install --no-cache-dir axolotl --no-deps
RUN pip install --no-cache-dir fire pydantic accelerate datasets

# ✅ Installer llama-cpp-python avec support CPU
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=OFF"
RUN git clone --recurse-submodules https://github.com/abetlen/llama-cpp-python.git && \
  cd llama-cpp-python && pip install .

# ========================== STAGE 1 : TRAIN ==========================
FROM python-base AS builder

COPY . ./
ENV PYTHONPATH=/app

RUN python scripts/prepare_dataset.py
RUN axolotl train model/axolotl-config.yaml && \
  axolotl merge model/final-checkpoint --output model/final-checkpoint/merged.gguf

# ========================== STAGE 2 : API ==========================
FROM python-base AS runner

COPY --from=builder /app/app ./app
COPY --from=builder /app/model/final-checkpoint ./model/final-checkpoint

ENV PYTHONPATH=/app

EXPOSE 8001
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
