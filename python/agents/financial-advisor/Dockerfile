FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry first
RUN pip install poetry && poetry config virtualenvs.create false

# Copy poetry files first for better caching
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-interaction --no-ansi --only=main

# Copy the rest of the application
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Use the startup script
CMD ["./start.sh"]