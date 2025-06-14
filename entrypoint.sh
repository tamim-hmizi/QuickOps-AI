#!/usr/bin/env bash
set -e

echo "[entrypoint] starting Ollama server..."
ollama serve &

echo "[entrypoint] waiting for Ollama..."
until ollama list &>/dev/null; do
  sleep 0.5
done

echo "[entrypoint] pulling llama3.2 model..."
ollama pull llama3.2

echo "[entrypoint] launching FastAPI on port 8001..."
uvicorn app:app --host 0.0.0.0 --port 8001
