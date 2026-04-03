FROM python:3.12-slim

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy everything first (needed for pip install -e)
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e "."

# Build frontend
RUN cd frontend && npm install && npm run build

ENV PORT=8000

# Use shell form so $PORT is expanded at runtime
CMD uvicorn backend.main:app --host 0.0.0.0 --port $PORT
