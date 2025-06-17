FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y build-essential

# Copy your project files
COPY . /app

# Install Poetry and project dependencies
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Cloud Run will provide the PORT environment variable
# Don't use EXPOSE as Cloud Run ignores it

# Start our custom FastAPI web server with CORS support
CMD ["poetry", "run", "python", "web_server.py"]