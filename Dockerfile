FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make the start script executable
RUN chmod +x /app/start.sh

# Expose the port
EXPOSE 8000

# Run the startup script (which runs alembic and then starts uvicorn)
CMD ["/app/start.sh"]
