FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend source
COPY backend/ /app/backend/

# Copy frontend
COPY frontend/ /app/frontend/

EXPOSE 8000

CMD ["sh", "-c", "cd /app/backend && python seed.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
