FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
  libopenblas-dev \
  curl \
  build-essential \
  cmake \
  git \
  ccache \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt \
  && pip install --no-cache-dir axolotl

# Copy project files
COPY ./app ./app
COPY ./data ./data
COPY ./model ./model
COPY ./scripts ./scripts

# Ensure Python can find all modules
ENV PYTHONPATH=/app

# Prepare training dataset
RUN python scripts/prepare_dataset.py

# Run fine-tuning with Axolotl
RUN axolotl train model/axolotl-config.yaml

# Merge LoRA adapters to GGUF
RUN axolotl merge model/final-checkpoint --output model/final-checkpoint/merged.gguf

# Expose API port
EXPOSE 8001

# Start the FastAPI application
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
