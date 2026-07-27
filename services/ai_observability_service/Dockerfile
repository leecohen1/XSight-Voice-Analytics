FROM python:3.11-slim

WORKDIR /service

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# The SQLite database (pricing_config + infrastructure_cost_config only —
# per-event telemetry is owned by Langfuse, not this file) lives under
# /service/data — mount a volume at this path in any real deployment so it
# survives a container restart (see docker-compose.yml). The directory is
# created automatically by app/db.py on first startup if it doesn't already
# exist.

EXPOSE 8005

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8005/health', timeout=2).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
