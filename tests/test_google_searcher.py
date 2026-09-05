import pytest
from playwright.async_api import async_playwright

from scraper.browser.google_searcher import GoogleSearcher


@pytest.mark.asyncio
async def test_google_searcher_finds_target_domain():

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        async def handle_route(route):
            await route.fulfill(
                status=200,
                content_type="text/html",
                body="""
                    <html>
                        <body>
                            <textarea name="q"></textarea>

                            <div id="search">
                                <a href="https://example.com/other">
                                    <h3>Otro resultado</h3>
                                    <cite class="tjvcx GvPZzd cHaqb">
                                        https://example.com
                                    </cite>
                                </a>

                                <a href="https://www.g2.com/es">
                                    <h3>Metric.ai Reviews</h3>
                                    <cite class="tjvcx GvPZzd cHaqb">
                                        https://www.g2.com
                                    </cite>
                                </a>
                            </div>
                        </body>
                    </html>
                """,
            )

        await page.route(
            "https://www.google.com/*",
            handle_route,
        )

        searcher = GoogleSearcher()

        result = await searcher.search(
            page,
            "Metric.ai",
            "https://www.g2.com/products/metric-ai/reviews",
        )

        assert result == (
            "https://www.g2.com/es"
        )

        await browser.close()
