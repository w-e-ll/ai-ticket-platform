FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY README.md .

RUN pip install --upgrade pip setuptools wheel

RUN pip install .

COPY . .

RUN mkdir -p \
    /app/logs \
    /app/uploads \
    /app/models

EXPOSE 8000
EXPOSE 8501

CMD ["uvicorn", "ai_ticket_platform.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
