import pytest
from playwright.async_api import Page, async_playwright

from scraper.base_scraper import BaseScraper
from scraper.scraping_runner import ScrapingRunner
from validation.product import Product
from validation.scraping_result import ScrapingResult


class FakeScraper(BaseScraper):
    """Scraper simulado para pruebas."""

    async def scrape(
        self,
        page: Page,
        url: str,
    ) -> ScrapingResult:

        product = Product(
            product_name="Metric.ai",
            product_url=url,
        )

        return ScrapingResult(
            product=product,
            access_status="success",
            attempts=1,
        )


@pytest.mark.asyncio
async def test_scraping_runner_executes_requested_samples():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        scraper = FakeScraper()

        runner = ScrapingRunner(
            scraper=scraper,
            sample_count=3,
        )

        results = await runner.run(
            page,
            "https://example.com/product",
        )

        assert len(results) == 3

        for result, execution_time in results:
            assert result.access_status == "success"
            assert result.product is not None
            assert result.product.product_name == "Metric.ai"
            assert execution_time >= 0

        await browser.close()