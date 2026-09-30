FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    cmake \
    pkg-config \
    libopus-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Application
COPY . .

# Runtime directories
RUN mkdir -p /app/output \
    /app/temp \
    /app/separated \
    /app/input

EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
