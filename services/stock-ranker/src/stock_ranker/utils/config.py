from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_explorer_url: str = "http://localhost:8000"
    db_path: Path = Path("stock_ranker.db")
    port: int = 8001

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
