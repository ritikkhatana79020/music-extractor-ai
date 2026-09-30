FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# System dependencies + Deno for yt-dlp YouTube JavaScript challenges
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    ffmpeg \
    git \
    build-essential \
    cmake \
    pkg-config \
    libopus-dev \
    && curl -fsSL https://deno.land/install.sh | sh \
    && ln -s /root/.deno/bin/deno /usr/local/bin/deno \
    && deno --version \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Application
COPY . .

# Runtime directories
RUN mkdir -p \
    /app/output \
    /app/temp \
    /app/separated \
    /app/input

EXPOSE 8000

CMD ["sh", "-c", "uvicorn api_server:app --host 0.0.0.0 --port ${PORT:-8000}"]