from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    api_explorer_url: str = "http://localhost:8000"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 600


config = Config()
