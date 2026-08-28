from playwright.async_api import Browser, Playwright

class BrowserManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright
        self.browser: Browser | None = None

    async def start(self, headless: bool = True) -> Browser:
        self.browser = await self.playwright.chromium.launch(
            headless=headless
        )
        return self.browser

    async def close(self) -> None:
        if self.browser:
            await self.browser.close()
            self.browser = None