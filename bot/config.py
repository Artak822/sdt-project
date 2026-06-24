from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TELEGRAM_BOT_TOKEN: str
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    REDIS_URL: str = "redis://localhost:6379/0"
    USER_SERVICE_URL: str = "http://user_service:8000"
    MATCH_SERVICE_URL: str = "http://match_service:8002"
    LOG_LEVEL: str = "INFO"

    S3_ENDPOINT_URL: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "dating-photos"
    S3_REGION: str = "us-east-1"
    S3_PUBLIC_BASE_URL: str | None = None
    S3_KEY_PREFIX: str = "photos"


settings = Settings()
