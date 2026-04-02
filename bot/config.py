from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TELEGRAM_BOT_TOKEN: str
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    USER_SERVICE_URL: str = "http://user_service:8000"
    LOG_LEVEL: str = "INFO"


settings = Settings()
