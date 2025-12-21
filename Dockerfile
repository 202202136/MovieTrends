# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set workdir
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app
COPY . /app

# Ensure database directory exists
RUN mkdir -p /app/data

# Create a non-root user and give ownership
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app

# Expose port and default listen port env
EXPOSE 5000
ENV PORT=5000
ENV FLASK_ENV=production

# Switch to non-root user
USER appuser

# Healthcheck (simple HTTP GET to /)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import os,sys,urllib.request; p=os.environ.get('PORT','5000'); url=f'http://127.0.0.1:{p}/'; r=urllib.request.urlopen(url, timeout=4); sys.exit(0 if r.status==200 else 1)" || exit 1

# Entrypoint: initialize DB then run Gunicorn bound to $PORT
CMD python -c "from data.db import init_db; init_db()" && exec gunicorn wsgi:app -b 0.0.0.0:${PORT} --workers 3
