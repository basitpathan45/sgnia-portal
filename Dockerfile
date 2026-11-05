FROM python:3.12-slim

# Install system packages needed for compiling if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Set working directory to /app
WORKDIR /app

# Copy requirements and install python packages
COPY staff_portal/requirements.txt staff_portal/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r staff_portal/requirements.txt

# Copy all project files
COPY . .

# Preserve Hugging Face Spaces' default while honoring Render's injected PORT.
ENV PORT=7860
EXPOSE 7860

# Prepare legacy databases and apply migrations before starting Gunicorn.
CMD ["sh", "-c", "cd staff_portal && flask --app run.py prepare-db && exec gunicorn --bind 0.0.0.0:${PORT:-7860} --workers 2 --timeout 120 run:app"]
