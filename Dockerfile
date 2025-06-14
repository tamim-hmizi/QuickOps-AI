FROM ollama/ollama:latest

WORKDIR /app
COPY entrypoint.sh /entrypoint.sh
COPY requirements.txt app.py ./

RUN chmod +x /entrypoint.sh
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8001 11434

ENTRYPOINT ["/entrypoint.sh"]
