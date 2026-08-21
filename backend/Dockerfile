FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# --timeout/--retries make the build resilient to slow/flaky PyPI links.
RUN pip install --no-cache-dir --timeout 120 --retries 10 -r requirements.txt

# Build stamp — lets a running container say WHICH code it is, so a deploy that
# pulled but never rebuilt is visible instead of silent. Set by scripts/deploy.sh.
ARG GIT_SHA=unknown
ARG BUILD_TIME=unknown
ENV APP_GIT_SHA=$GIT_SHA
ENV APP_BUILD_TIME=$BUILD_TIME

# Copy application code
COPY . .

# Create directories that the app writes to at runtime
RUN mkdir -p logs uploads/personnel_photos uploads/meeting_qr media/mtd \
    media/custom-attributes media/onboardings media/resignations

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

# Production: no --reload, explicit host binding.
# --proxy-headers + --forwarded-allow-ips lets uvicorn trust nginx's
# X-Forwarded-Proto so request.url.scheme is https behind TLS — otherwise
# FastAPI trailing-slash 307 redirects point to http:// and the browser blocks
# them as mixed content.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
