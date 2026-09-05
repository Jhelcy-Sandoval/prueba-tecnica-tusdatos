from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centraliza la configuración del scraper y su estrategia de ejecución."""

    target_url: str
    search_query: str
    g2_search_query: str | None = None

    headless: bool = False

    sample_count: int = 3
    sample_delay: float = 2.0

    max_attempts: int = 3
    base_delay: float = 2.0
    manual_intervention_delay: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )