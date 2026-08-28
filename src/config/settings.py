from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    target_url: str
    headless: bool = True
    timeout: int = 30000
    sample_count: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )