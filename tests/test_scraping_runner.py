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
            products=[product],
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

        for sample_id, result, execution_time in results:
            assert sample_id in (1, 2, 3)
            assert result.access_status == "success"
            assert len(result.products) == 1
            assert result.products[0].product_name == "Metric.ai"
            assert execution_time >= 0

        assert [sample_id for sample_id, _, _ in results] == [1, 2, 3]

        await browser.close()