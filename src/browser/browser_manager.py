from playwright.sync_api import Browser, Playwright

class BrowserManager:
    def __init__(self, playwright):
        self.playwright = playwright
        self.browser = None

    def start(self, headless: bool = True):
        self.browser = self.playwright.chromium.launch(
            headless=headless
        )
        return self.browser

    def close(self):
        if self.browser:
            self.browser.close()