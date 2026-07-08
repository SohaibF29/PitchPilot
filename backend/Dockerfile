# Multi-stage Docker build for PitchPilot backend
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies needed for WeasyPrint/compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install python builder tool and copy definitions
RUN pip install --no-cache-dir hatchling

COPY pyproject.toml .

# Install dependencies into separate cacheable virtual environment
RUN pip install --no-cache-dir .

# Stage 2: Final minimal image
FROM python:3.11-slim

WORKDIR /app

# Install WeasyPrint shared library runtimes
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python environments from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY app app

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
