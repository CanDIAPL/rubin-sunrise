# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies, including PostgreSQL
RUN apt-get update && apt-get install -y \
    postgresql \
    postgresql-contrib \
    build-essential \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create PostgreSQL data directory
RUN mkdir -p /var/run/postgresql && \
    chown postgres:postgres /var/run/postgresql && \
    mkdir -p /var/lib/postgresql/data && \
    chown postgres:postgres /var/lib/postgresql/data && \
    mkdir -p /var/lib/postgresql/custom_storage && \
    chown postgres:postgres /var/lib/postgresql/custom_storage && \
    chmod 700 /var/lib/postgresql/custom_storage

# Expose Flask port
EXPOSE 8000

# Run the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
