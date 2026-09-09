FROM python:3.11-slim

# Install system binaries: LibreOffice for docx->pdf and FFmpeg for media extraction
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    ffmpeg \
    fonts-liberation \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

ENV PORT=5000
EXPOSE 5000

# Execute Gunicorn using shell form so $PORT is dynamically evaluated by Render
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 app:app
