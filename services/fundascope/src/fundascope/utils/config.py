from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    host: str = "0.0.0.0"
    port: int = 8001
    api_explorer_url: str = "http://localhost:8000"
    stock_ranker_url: str = "http://localhost:8001"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 600


config = Config()
