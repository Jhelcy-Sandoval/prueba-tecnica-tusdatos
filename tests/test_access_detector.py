import pytest
from playwright.async_api import async_playwright

from resilience.access_detector import AccessDetector
from resilience.access_result import (
    AccessBlocked,
    AccessGranted,
    CaptchaRequired,
)


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

        result = await detector.detect(page)

        assert isinstance(result, AccessGranted)
        assert result.status == "success"

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

        result = await detector.detect(page)

        assert isinstance(result, CaptchaRequired)
        assert result.status == "captcha"

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

        result = await detector.detect(page)

        assert isinstance(result, AccessBlocked)
        assert result.status == "blocked"

        await browser.close()