FROM python:3.12-slim

WORKDIR /app

# System packages needed by geospatial/Python dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libgeos-dev \
    libproj-dev \
    proj-data \
    proj-bin \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Render provides PORT at runtime
ENV PYTHONUNBUFFERED=1

# Start FastAPI
CMD sh -c 'uvicorn server.src.app:app --host 0.0.0.0 --port ${PORT:-8000}'