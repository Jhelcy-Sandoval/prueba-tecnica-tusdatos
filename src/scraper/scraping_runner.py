import asyncio
import time
from dataclasses import dataclass, field

from playwright.async_api import Page

from scraper.base_scraper import BaseScraper
from validation.scraping_result import ScrapingResult


@dataclass
class ScrapingRunner:
    """Ejecuta múltiples muestras utilizando un scraper"""

    scraper: BaseScraper
    sample_count: int = 1
    sample_delay: float = 2.0
    results: list[
        tuple[ScrapingResult, float]
    ] = field(default_factory=list)

    async def run(
        self,
        page: Page,
        url: str,
    ) -> list[tuple[ScrapingResult, float]]:
        """Ejecuta las muestras y mide su tiempo."""

        self.results.clear()

        for sample in range(self.sample_count):

            print(
                f"Muestra {sample + 1}/"
                f"{self.sample_count}"
            )

            start_time = time.perf_counter()

            result = await self.scraper.scrape(
                page,
                url,
            )

            execution_time = (
                time.perf_counter() - start_time
            )

            self.results.append(
                (result, execution_time)
            )

            if sample < self.sample_count - 1:
                await asyncio.sleep(self.sample_delay)

        return self.results