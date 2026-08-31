FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable buffered stdout/stderr for logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose the port the app runs on (PaaS providers inject $PORT at runtime)
EXPOSE 8000

# Default port 8000, overridable via $PORT for Render/Railway dynamic ports
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
