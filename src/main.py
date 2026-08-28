from playwright.sync_api import sync_playwright

from browser.browser_manager import BrowserManager
from config.settings import Settings


def main():
    settings = Settings()

    with sync_playwright() as playwright:
        browser_manager = BrowserManager(playwright)

        browser = browser_manager.start(headless=False)

        page = browser.new_page()

        page.goto(settings.target_url)

        print(f"Título: {page.title()}")
        print(f"URL: {page.url}")

        browser_manager.close()


if __name__ == "__main__":
    main()