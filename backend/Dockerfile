FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
# Install poetry and setuptools
RUN pip install --no-cache-dir poetry==1.8.3 setuptools

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no dev)
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main --no-interaction --no-ansi

# Ensure setuptools with pkg_resources is available (OpenTelemetry compatibility)
# Version < 70 is safer for pkg_resources stability
RUN pip install --no-cache-dir "setuptools<70"

# Verify pkg_resources availability
RUN python -c "import pkg_resources; print('pkg_resources is available')"

# Pre-download SentenceTransformer model (all-MiniLM-L6-v2)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
