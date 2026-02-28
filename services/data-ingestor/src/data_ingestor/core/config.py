from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_explorer_url: str = "http://localhost:8000"
    db_dsn: str = "postgresql://postgres:postgres@localhost:5432/stock_data"
    host: str = "0.0.0.0"
    port: int = 8001

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
