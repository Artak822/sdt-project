FROM python:3.11-slim
WORKDIR /app
COPY celery_worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["celery", "-A", "celery_worker.celery_app", "worker", "--beat", "--loglevel=info"]
