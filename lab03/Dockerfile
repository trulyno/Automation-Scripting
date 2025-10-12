FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY currency_exchange_rate.py /app/

RUN pip install --no-cache-dir requests

COPY cronjob /etc/cron.d/currency-cron

RUN chmod 0644 /etc/cron.d/currency-cron

RUN crontab /etc/cron.d/currency-cron

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

RUN mkdir -p /app/data

ENTRYPOINT ["/entrypoint.sh"]
