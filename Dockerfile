FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
# pip, setuptools and wheel are only needed to install; removing them keeps
# their vendored packages out of the runtime image.
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y pip setuptools wheel && \
    rm -rf /usr/local/lib/python3.11/ensurepip

COPY app.py .

RUN useradd --system --uid 10001 app
USER app

EXPOSE 8001
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
