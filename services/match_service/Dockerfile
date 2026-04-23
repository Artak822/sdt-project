FROM python:3.11-slim
WORKDIR /app
COPY services/match_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "services.match_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
