# Use official Python base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    openssl \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Generate prisma client (without specific schema path)
RUN prisma generate

# Create non-root user
RUN useradd -m -u 1000 litellm && chown -R litellm:litellm /app

# Switch to non-root user  
USER litellm

# Make entrypoint executable
RUN chmod +x docker/prod_entrypoint.sh

# Expose port
EXPOSE 4000

# Use official entrypoint
ENTRYPOINT ["docker/prod_entrypoint.sh"]
CMD ["--config", "/app/config_fixed_cache.yaml", "--port", "4000"]
