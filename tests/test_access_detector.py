import pytest
from playwright.async_api import async_playwright

from resilience.access_detector import AccessDetector, AccessStatus


@pytest.mark.asyncio
async def test_detect_success():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.set_content("""
            <html>
                <body>
                    <h1>Producto de prueba</h1>
                </body>
            </html>
        """)

        detector = AccessDetector()

        status = await detector.detect(page)

        assert status == AccessStatus.SUCCESS

        await browser.close()


@pytest.mark.asyncio
async def test_detect_captcha():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.set_content("""
            <html>
                <body>
                    <iframe
                        title="DataDome CAPTCHA"
                        src="https://geo.captcha-delivery.com/captcha/">
                    </iframe>
                </body>
            </html>
        """)

        detector = AccessDetector()

        status = await detector.detect(page)

        assert status == AccessStatus.CAPTCHA

        await browser.close()


@pytest.mark.asyncio
async def test_detect_blocked():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.set_content("""
            <html>
                <body>
                    <h1>Access Denied</h1>
                </body>
            </html>
        """)

        detector = AccessDetector()

        status = await detector.detect(page)

        assert status == AccessStatus.BLOCKED

        await browser.close()