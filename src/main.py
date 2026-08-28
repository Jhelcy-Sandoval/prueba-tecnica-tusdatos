import asyncio

from playwright.async_api import async_playwright

from browser.browser_manager import BrowserManager
from config.settings import Settings
from persistence.dataset_writer import DatasetWriter
from scraper.g2.g2_scraper import G2Scraper


async def main():
    settings = Settings()
    dataset_writer = DatasetWriter()

    async with async_playwright() as playwright:
        browser_manager = BrowserManager(playwright)

        browser = await browser_manager.start(
            headless=settings.headless
        )

        page = await browser.new_page()

        scraper = G2Scraper()

        result = await scraper.scrape(
            page,
            settings.target_url,
        )

        print(result)

        if result.product is not None:
            dataset_writer.save(result.product)

            print("Producto guardado en el dataset.")

        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(main())