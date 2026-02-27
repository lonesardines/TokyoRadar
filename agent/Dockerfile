FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY shared/ /shared/
RUN pip install --no-cache-dir /shared

COPY agent/requirements.txt /app/agent-requirements.txt
RUN pip install --no-cache-dir -r /app/agent-requirements.txt

COPY agent/ /app/agent/

RUN mkdir -p /app/sessions

CMD ["celery", "-A", "agent.celery_app", "worker", "--loglevel=info", "-Q", "agent"]
