import asyncio
import time

from playwright.async_api import Page

from browser.browser_manager import BrowserManager
from scraper.base_scraper import BaseScraper
from scraper.browser.google_searcher import GoogleSearcher


class ScrapingRunner:
    '''
    Coordina la ejecución de las muestras configuradas
    y entrega cada resultado individualmente.
    '''

    def __init__(
        self,
        scraper: BaseScraper,
        google_searcher: GoogleSearcher | None,
        browser_manager: BrowserManager,
        sample_count: int,
        sample_delay: float,
    ):
        '''
        Inicializa el runner con las dependencias necesarias
        para ejecutar las muestras.
        '''

        self.scraper = scraper
        self.google_searcher = google_searcher
        self.browser_manager = browser_manager
        self.sample_count = sample_count
        self.sample_delay = sample_delay

    async def run(
        self,
        page: Page,
        query: str,
        target_url: str | None = None,
        start_sample_id: int = 1,
    ):
        '''
        Ejecuta las muestras configuradas y entrega cada resultado
        inmediatamente después de finalizar su ejecución.
        '''

        batch_size = 5

        for index in range(
            self.sample_count
        ):

            sample_id = (
                start_sample_id + index
            )

            if index > 0 and index % batch_size == 0:

                print(
                    "\nSe completaron 5 muestras."
                )

                print(
                    "Eliminando el contexto actual..."
                )

                await self.browser_manager.destroy_context()

                print(
                    "Creando un nuevo contexto..."
                )

                context = await self.browser_manager.start(
                    headless=self.browser_manager.settings.headless,
                    use_proxy=False,
                )

                page = await context.new_page()

                self.browser_manager.page = page

                print(
                    "Nuevo contexto creado."
                )

            if target_url is None:
                url = query

            elif self.google_searcher:

                print(
                    "\nIniciando búsqueda desde Google..."
                )

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

                    return

                print(
                    "Resultado objetivo encontrado. "
                    "Iniciando extracción."
                )

            else:
                url = target_url

            print(
                f"\nMuestra {sample_id}/"
                f"{start_sample_id + self.sample_count - 1}"
            )

            if self.browser_manager.page:
                page = self.browser_manager.page

            start_time = time.perf_counter()

            result = await self.scraper.scrape(
                page,
                url,
                self.browser_manager,
            )

            if self.browser_manager.page:
                page = self.browser_manager.page

            execution_time = (
                time.perf_counter()
                - start_time
            )

            yield (
                sample_id,
                result,
                execution_time,
            )

            if self.sample_delay > 0:
                await asyncio.sleep(
                    self.sample_delay
                )

        print(
            "\nFinalizaron todas las muestras."
        )