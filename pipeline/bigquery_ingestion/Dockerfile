FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if needed, e.g., for gzip)
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingest_data_bigquery.py .

# Run the script – arguments will be passed at runtime
ENTRYPOINT ["python", "ingest_data_bigquery.py"]