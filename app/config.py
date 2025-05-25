from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    model_config = ConfigDict(case_sensitive=True, env_file=".env", env_file_encoding="utf-8", extra="allow")


class Config(BaseConfig):
    DEBUG: bool

    OLLAMA_HOST: str


config: Config = Config()
