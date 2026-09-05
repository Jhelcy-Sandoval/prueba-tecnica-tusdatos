from abc import ABC, abstractmethod

from playwright.async_api import Page

from validation.scraping_result import ScrapingResult


class BaseScraper(ABC):
    '''
    Define el contrato base para los componentes encargados
    de ejecutar procesos de scraping.
    '''

    @abstractmethod
    async def scrape(
        self,
        page: Page,
        url: str,
    ) -> ScrapingResult:
        '''
        Ejecuta el proceso de extracción y retorna el resultado
        de la ejecución del scraper.
        '''

        raise NotImplementedError