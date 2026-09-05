import pytest
from playwright.async_api import async_playwright

from scraper.g2.g2_extractor import G2Extractor


@pytest.mark.asyncio
async def test_extract_product_name():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.set_content("""
            <html>
                <body>
                    <h1>Metric.ai Reviews & Product Details</h1>
                </body>
            </html>
        """)

        extractor = G2Extractor()

        result = await extractor.extract(page)

        assert result["product_name"] == "Metric.ai"

        await browser.close()


@pytest.mark.asyncio
async def test_extract_dismisses_login_overlay():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.set_content("""
            <h1>Metric.ai Reviews</h1>
            <dialog id="login-overlay" open>
                <button
                    data-action="elv--modal-controller#close"
                    onclick="this.closest('dialog').close()"
                >
                    Cerrar
                </button>
            </dialog>
        """)

        result = await G2Extractor().extract(page)

        assert result["product_name"] == "Metric.ai"
        assert await page.locator("dialog#login-overlay[open]").count() == 0

        await browser.close()
