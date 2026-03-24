# ── Stage 1: Builder ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a separate directory
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first
RUN useradd -m appuser

# Copy dependencies and app
COPY --from=builder /install /usr/local
COPY . .

# Create instance folder and fix ownership
RUN mkdir -p /app/instance && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 5000

# Start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
