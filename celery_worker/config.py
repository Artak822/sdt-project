from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/dating"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
