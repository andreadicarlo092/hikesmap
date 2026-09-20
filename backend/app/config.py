from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://trail:trail@db:5432/trailexplorer"
    DATABASE_URL_SYNC: str = "postgresql://trail:trail@db:5432/trailexplorer"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
