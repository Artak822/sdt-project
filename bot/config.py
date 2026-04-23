from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TELEGRAM_BOT_TOKEN: str
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    REDIS_URL: str = "redis://localhost:6379/0"
    USER_SERVICE_URL: str = "http://user_service:8000"
    MATCH_SERVICE_URL: str = "http://match_service:8002"
    LOG_LEVEL: str = "INFO"


settings = Settings()
