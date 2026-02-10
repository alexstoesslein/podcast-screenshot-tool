FROM python:3.11-slim

# Install system dependencies for OpenCV and video processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

# Copy application code
COPY src/ ./src/
COPY web/ ./web/

# Create uploads directory
RUN mkdir -p web/uploads

EXPOSE 10000
CMD ["gunicorn", "web.app:app", "--bind", "0.0.0.0:10000", "--timeout", "600", "--workers", "2"]
