FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY shared/ /shared/
RUN pip install --no-cache-dir /shared

COPY ai_pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ai_pipeline/ /app/ai_pipeline/

CMD ["celery", "-A", "ai_pipeline.celery_app", "worker", "--loglevel=info", "-Q", "ai"]
