FROM python:3.12-slim-bookworm

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies:
#   - default-libmysqlclient-dev + gcc: needed to build mysqlclient C extension (used by PyMySQL compat layer)
#   - netcat-openbsd: used in docker-entrypoint.sh to wait for MySQL to be ready
#   - curl: useful for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        default-libmysqlclient-dev \
        pkg-config \
        netcat-openbsd \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (including gunicorn for production serving)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir gunicorn==23.0.0 \
    && pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Ensure the entrypoint script is executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose the Gunicorn port
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD ["gunicorn", "adv_hotel_mgmt.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]