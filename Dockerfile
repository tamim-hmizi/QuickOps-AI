FROM python:3.10-slim

WORKDIR /app

COPY . /app

COPY .env /app/.env

RUN pip install --upgrade pip \
  && pip install -r requirements.txt

EXPOSE 8001

HEALTHCHECK --interval=60s --timeout=60s --start-period=60s --retries=10 \
  CMD curl --fail http://localhost:8001/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
