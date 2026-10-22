# ── Backend Dockerfile ──
# Uses dlib-bin (pre-compiled) so no heavy compilation needed
FROM python:3.11-slim

# Install minimal system dependencies for OpenCV headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
# Step 1: upgrade pip + install base requirements
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
# Step 2: install pre-compiled dlib (no cmake/compilation needed)
RUN pip install --no-cache-dir dlib-bin
# Step 3: install face-recognition WITHOUT pulling source dlib as dependency
RUN pip install --no-cache-dir face-recognition --no-deps
# Step 4: install face_recognition_models (needed by face-recognition)
RUN pip install --no-cache-dir face_recognition_models

# Copy application code
COPY . .

# Create runtime directories
RUN mkdir -p uploads thumbnails temp

# Render sets PORT env var; default to 8001 locally
ENV PORT=8001
EXPOSE ${PORT}

# Start server — uses $PORT so Render can assign its own port
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
