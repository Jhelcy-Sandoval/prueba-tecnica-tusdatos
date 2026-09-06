import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    target_url: str
    search_query: str
    g2_search_query: str | None = None
    headless: bool = False
    sample_count: int = 3
    sample_delay: float = 2.0
    max_attempts: int = 3
    base_delay: float = 2.0
    manual_intervention_delay: float = 30.0
    browser: str = "chromium"
    browser_path: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def proxies(self) -> list[str]:
        """Obtiene los proxies configurados desde el archivo JSON."""
        proxy_file = Path("config/proxies.json")

        if not proxy_file.exists():
            print(
                f"No existe el archivo de proxies: "
                f"{proxy_file.resolve()}"
            )
            return []

        with proxy_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return [
            proxy.strip()
            for proxy in data.get("proxies", [])
            if proxy.strip()
        ]