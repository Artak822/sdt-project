FROM python:3.11-slim
WORKDIR /app
COPY services/rating_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "services.rating_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
