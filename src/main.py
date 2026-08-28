import asyncio

from playwright.async_api import async_playwright

from browser.browser_manager import BrowserManager
from config.settings import Settings
from metrics.scraper_metrics import ScraperMetrics
from persistence.dataset_writer import DatasetWriter
from scraper.g2.g2_scraper import G2Scraper
from scraper.scraping_runner import ScrapingRunner


async def main():
    settings = Settings()

    dataset_writer = DatasetWriter()
    metrics = ScraperMetrics()

    async with async_playwright() as playwright:
        browser_manager = BrowserManager(playwright)

        browser = await browser_manager.start(
            headless=settings.headless
        )

        page = await browser.new_page()

        scraper = G2Scraper()

        runner = ScrapingRunner(
            scraper=scraper,
            sample_count=3,
        )

        results = await runner.run(
            page,
            settings.target_url,
        )

        for result, execution_time in results:

            print(result)

            metrics.record(
                result,
                execution_time,
            )

            if result.product is not None:
                dataset_writer.save(
                    result.product
                )

        print("Métricas:")
        print(metrics.summary())

        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(main())