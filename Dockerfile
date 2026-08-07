FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        smartmontools \
        util-linux \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    -r requirements.txt

COPY src ./src
COPY config ./config

RUN mkdir -p /app/sample-output

CMD ["python", "-m", "homelab_guardian"]