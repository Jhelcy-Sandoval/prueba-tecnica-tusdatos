import pytest
from playwright.async_api import async_playwright

from scraper.g2.g2_scraper import G2Scraper


@pytest.mark.asyncio
async def test_g2_scraper_success():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        async def handle_route(route):
            await route.fulfill(
                status=200,
                content_type="text/html",
                body="""
                    <html>
                        <body>
                            <h1>
                                Metric.ai Reviews & Product Details
                            </h1>
                        </body>
                    </html>
                """,
            )

        await page.route(
            "https://example.com/products/metric-ai/reviews",
            handle_route,
        )

        scraper = G2Scraper()

        result = await scraper.scrape(
            page,
            "https://example.com/products/metric-ai/reviews",
        )

        assert result.access_status == "success"
        assert result.attempts == 1

        assert result.product is not None
        assert result.product.product_name == "Metric.ai"
        assert str(result.product.product_url) == (
            "https://example.com/products/metric-ai/reviews"
        )

        await browser.close()