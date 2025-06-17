#!/bin/bash

# Set default port if not provided
export PORT=${PORT:-8000}
export HOST=${HOST:-0.0.0.0}

echo "Starting Financial Advisor API..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "Python version: $(python --version)"

# Start the application
exec uvicorn web_server:app --host "$HOST" --port "$PORT" --log-level info 