FROM python:3.11-slim

WORKDIR /service

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Only the schema file itself is needed at runtime (app/filters.py's
# allowlist source) — not the rest of services/rag_service/ingestion/
# (conversion/validation scripts, generated output), which are dev-time
# tooling only.
COPY ingestion/metadata_schema.json ./ingestion/metadata_schema.json

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8001/health', timeout=2).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
