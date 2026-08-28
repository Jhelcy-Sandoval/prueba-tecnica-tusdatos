from enum import Enum

from playwright.async_api import Page


class AccessStatus(Enum):
    # estados posibles
    SUCCESS = "success"
    CAPTCHA = "captcha"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class AccessDetector:
    # detector del estado de la pagina

    async def detect(self, page: Page) -> AccessStatus:
        content = (await page.content()).lower()

        if "datadome captcha" in content or "captcha-delivery.com" in content:
            return AccessStatus.CAPTCHA

        if "access denied" in content or "access blocked" in content:
            return AccessStatus.BLOCKED

        return AccessStatus.SUCCESS