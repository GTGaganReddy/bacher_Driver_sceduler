# Cloud Run Dockerfile for Driver Scheduling Backend
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application code
COPY . .

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Use the optimized startup script
CMD ["python", "start.py"]