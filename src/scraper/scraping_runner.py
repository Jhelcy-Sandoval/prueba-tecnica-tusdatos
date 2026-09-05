import asyncio
import time
from dataclasses import dataclass, field

from playwright.async_api import Page

from scraper.base_scraper import BaseScraper
from scraper.browser.google_searcher import GoogleSearcher
from validation.scraping_result import ScrapingResult


@dataclass
class ScrapingRunner:
    '''
    Ejecuta múltiples muestras de scraping, controla su
    secuencia y registra el tiempo de cada ejecución.
    '''

    scraper: BaseScraper
    google_searcher: GoogleSearcher | None = None
    sample_count: int = 1
    sample_delay: float = 2.0
    results: list[
        tuple[int, ScrapingResult, float]
    ] = field(default_factory=list)

    async def run(
        self,
        page: Page,
        query: str,
        target_url: str | None = None,
    ) -> list[tuple[int, ScrapingResult, float]]:
        '''
        Ejecuta las muestras configuradas, mide el tiempo de
        cada ejecución y almacena sus resultados junto con
        el identificador de muestra.
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

        for sample in range(self.sample_count):

            sample_id = sample + 1

            print(
                f"Muestra {sample_id}/"
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