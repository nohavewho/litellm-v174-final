# Use the official Python image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (includes litellm[proxy]==1.74.3)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create non-root user
RUN useradd -m -u 1000 litellm && chown -R litellm:litellm /app

# Switch to non-root user
USER litellm

# Expose port
EXPOSE 4000

# DEBUG: Print environment variables before starting
CMD ["sh", "-c", "echo 'DEBUG: DATABASE_URL=' && echo $DATABASE_URL && echo 'DEBUG: All env vars:' && env | grep -E '(DATABASE|REDIS|LITELLM)' && python /app/gemini_filter_patch.py && litellm --config config_fixed_cache.yaml --host 0.0.0.0 --port 4000"]
