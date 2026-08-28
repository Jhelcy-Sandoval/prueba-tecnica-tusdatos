from abc import ABC, abstractmethod

from playwright.async_api import Page


class BaseScraper(ABC):
    # base para los scrapers
    @abstractmethod
    async def scrape(self, page: Page, url: str):
        """Extrae información desde una URL."""
        raise NotImplementedError