from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "TerraTwin Kenya API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    AZURE_SQL_SERVER: str = ""
    AZURE_SQL_DATABASE: str = ""
    AZURE_SQL_USER: str = ""
    AZURE_SQL_PASSWORD: str = ""

    CORS_ORIGINS: list[str] = ["http://localhost:4200"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()