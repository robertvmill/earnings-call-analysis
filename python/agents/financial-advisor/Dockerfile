FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry && poetry config virtualenvs.create false

# Copy poetry files first for better caching
COPY pyproject.toml poetry.lock ./

# Install Python dependencies
RUN poetry install --no-interaction --no-ansi --only=main

# Copy application code
COPY . .

# Cloud Run will provide the PORT environment variable
ENV PORT=8000

# Start the application
CMD exec uvicorn web_server:app --host 0.0.0.0 --port $PORT