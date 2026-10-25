FROM python:3.11-slim

# Install system dependencies: FFmpeg, libass, harfbuzz, and fonts including Google Noto for Indic scripts
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libavcodec-extra \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-noto-hinted \
    fonts-deva \
    fonts-taml \
    fonts-telu \
    fonts-knda \
    fonts-beng \
    fonts-gujr \
    fonts-guru \
    fonts-mlym \
    fonts-orya \
    libraqm0 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
