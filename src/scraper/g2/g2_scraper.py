import asyncio

from playwright.async_api import Page

from resilience.access_detector import AccessDetector, AccessStatus
from resilience.exceptions import (
    AccessBlockedError,
    CaptchaDetectedError,
    NavigationError,
)
from resilience.retry_policy import RetryPolicy
from scraper.base_scraper import BaseScraper
from scraper.g2.g2_extractor import G2Extractor
from validation.product import Product


class G2Scraper(BaseScraper):
    """Gestiona el proceso de scraping de G2."""

    def __init__(self):
        self.access_detector = AccessDetector()
        self.retry_policy = RetryPolicy()
        self.extractor = G2Extractor()

    async def scrape(self, page: Page, url: str):

        for attempt in range(self.retry_policy.max_attempts):

            print(
                f"Intento {attempt + 1}/"
                f"{self.retry_policy.max_attempts}"
            )

            try:
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                )

                status = await self.access_detector.detect(page)

                print(f"Estado de acceso: {status.value}")

                self._validate_access(status)

                data = await self.extractor.extract(page)

                product = Product(**data)

                return {
                    "data": product.model_dump(mode="json"),
                    "access_status": status.value,
                    "attempts": attempt + 1,
                }

            except (
                CaptchaDetectedError,
                AccessBlockedError,
                NavigationError,
            ) as error:

                print(f"Error: {error}")

                if not self.retry_policy.should_retry(attempt + 1):
                    return {
                        "product_url": page.url,
                        "access_status": "failed",
                        "failure_reason": type(error).__name__,
                        "attempts": attempt + 1,
                    }

                delay = self.retry_policy.get_delay(attempt)

                print(
                    f"Reintentando en {delay} segundos..."
                )

                await asyncio.sleep(delay)

    def _validate_access(self, status: AccessStatus) -> None:
        if status == AccessStatus.CAPTCHA:
            raise CaptchaDetectedError(
                "G2 devolvió un desafío CAPTCHA."
            )

        if status == AccessStatus.BLOCKED:
            raise AccessBlockedError(
                "G2 bloqueó el acceso."
            )

        if status == AccessStatus.UNKNOWN:
            raise NavigationError(
                "No se pudo determinar el estado de acceso."
            )