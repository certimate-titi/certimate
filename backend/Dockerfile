FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg and pymupdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Cloud Run sets PORT env var (default 8080)
ENV PORT=8080

EXPOSE 8080

# Entrypoint runs migrations then starts uvicorn
CMD ["./entrypoint.sh"]
