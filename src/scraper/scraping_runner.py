import asyncio
import time
from dataclasses import dataclass, field

from playwright.async_api import Page

from browser.browser_manager import BrowserManager
from scraper.base_scraper import BaseScraper
from scraper.browser.google_searcher import GoogleSearcher
from validation.scraping_result import ScrapingResult


@dataclass
class ScrapingRunner:
    '''
    Ejecuta múltiples muestras utilizando un scraper.
    '''

    scraper: BaseScraper
    google_searcher: GoogleSearcher | None = None
    browser_manager: BrowserManager | None = None
    sample_count: int = 1
    sample_delay: float = 2.0
    results: list[tuple[int, ScrapingResult, float]] = field(
        default_factory=list
    )

    async def run(
        self,
        page: Page,
        query: str,
        target_url: str | None = None,
    ) -> list[tuple[int, ScrapingResult, float]]:
        '''
        Ejecuta las muestras configuradas y registra
        el tiempo de ejecución de cada extracción.
        '''

        self.results.clear()

        if target_url is None:
            url = query

        elif self.google_searcher:
            url = await self.google_searcher.search(
                page,
                query,
                target_url,
            )

            if not url:
                print(
                    "No se encontró un resultado "
                    "para el dominio objetivo."
                )

                return []

            print(
                "Resultado objetivo encontrado. "
                "Iniciando extracción."
            )

        else:
            url = target_url

        for sample in range(
            self.sample_count
        ):
            sample_id = sample + 1

            print(
                f"Muestra {sample_id}/"
                f"{self.sample_count}"
            )

            start_time = time.perf_counter()

            result = await self.scraper.scrape(
                page,
                url,
                self.browser_manager,
            )

            if (
                self.browser_manager
                and self.browser_manager.page
            ):
                page = self.browser_manager.page

            execution_time = (
                time.perf_counter()
                - start_time
            )

            self.results.append(
                (
                    sample_id,
                    result,
                    execution_time,
                )
            )

            if sample < self.sample_count - 1:
                await asyncio.sleep(
                    self.sample_delay
                )

        return self.results