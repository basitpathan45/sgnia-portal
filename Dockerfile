FROM python:3.12-slim

# Install system packages needed for compiling if any
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory to /app
WORKDIR /app

# Copy requirements and install python packages
COPY staff_portal/requirements.txt staff_portal/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r staff_portal/requirements.txt

# Copy all project files
COPY . .

# Hugging Face Spaces listens on port 7860
ENV PORT=7860
EXPOSE 7860

# Start Flask with Gunicorn on 0.0.0.0:7860
CMD ["gunicorn", "--chdir", "staff_portal", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "120", "run:app"]
