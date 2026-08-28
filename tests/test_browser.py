import pytest
from playwright.async_api import async_playwright

from browser.browser_manager import BrowserManager


@pytest.mark.asyncio
async def test_browser_manager_starts_and_closes():
    async with async_playwright() as playwright:
        browser_manager = BrowserManager(playwright)

        browser = await browser_manager.start(headless=True)

        assert browser is not None

        await browser_manager.close()

        assert browser_manager.browser is None