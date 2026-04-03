FROM python:3.12-slim

# Install Node.js for frontend build + Claude Code CLI
RUN apt-get update && apt-get install -y curl git && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally (needed by Agent SDK)
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app

# Copy everything first (needed for pip install)
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir "."

# Build frontend
RUN cd frontend && npm install && npm run build

# Create workspace directory for generated projects
RUN mkdir -p /workspaces

ENV PORT=8000

# Use shell form so $PORT is expanded at runtime
CMD uvicorn backend.main:app --host 0.0.0.0 --port $PORT
