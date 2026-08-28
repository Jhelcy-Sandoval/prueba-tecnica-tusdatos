import asyncio

from playwright.async_api import async_playwright

from browser.browser_manager import BrowserManager
from config.settings import Settings
from scraper.g2_scraper import G2Scraper


async def main():
    settings = Settings()

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

        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(main())