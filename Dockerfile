FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -y \
  libopenblas-dev \
  curl \
  build-essential \
  cmake \
  git \
  ccache \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt ./ 
RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt \
  && pip install --no-cache-dir axolotl  # install axolotl for training

# Copy code
COPY ./app ./app
COPY ./data ./data
COPY ./model ./model
COPY ./scripts ./scripts

# ✅ Fix Python path so that `app.` imports work
ENV PYTHONPATH=/app

# Generate training dataset jsonl file
RUN python ./scripts/prepare_dataset.py

# Run fine-tuning with Axolotl
RUN axolotl train ./model/axolotl-config.yaml

# Merge LoRA adapters into GGUF file
RUN axolotl merge ./model/final-checkpoint --output ./model/final-checkpoint/merged.gguf

# Expose API port
EXPOSE 8001

# Run the FastAPI app
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
