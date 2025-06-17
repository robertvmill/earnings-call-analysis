FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y build-essential

# Copy your project files
COPY . /app

# Install Poetry and project dependencies
RUN pip install poetry && poetry install --no-interaction --no-ansi

# Expose the port your app runs on
EXPOSE 8000

# Start our custom FastAPI web server with CORS support
CMD ["poetry", "run", "python", "web_server.py"]