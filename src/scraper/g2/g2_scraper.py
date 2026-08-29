import asyncio

from playwright.async_api import Page

from config.settings import Settings
from integrations.captcha_provider import CaptchaProvider
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
from validation.scraping_result import ScrapingResult


class G2Scraper:

    def __init__(self, settings: Settings):
        self.access_detector = AccessDetector()
        self.retry_policy = RetryPolicy.from_settings(settings)
        self.extractor = G2Extractor()
        self.captcha_provider = CaptchaProvider()

    async def scrape(
        self,
        page: Page,
        url: str,
    ) -> ScrapingResult:

        for attempt in range(
            self.retry_policy.max_attempts
        ):

            print(
                f"Muestra de intento "
                f"{attempt + 1}/"
                f"{self.retry_policy.max_attempts}"
            )

            try:
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                )

                status = await self.access_detector.detect(
                    page
                )

                print(
                    f"Estado de acceso: {status.value}"
                )

                if status == AccessStatus.CAPTCHA:

                    print(
                        "CAPTCHA detectado. "
                        "Buscando intervención autorizada..."
                    )

                    found = await self.captcha_provider.solve(
                        page
                    )

                    if found:

                        print(
                            "captcha resuelto",
                            found,
                        )

                        status = AccessStatus.SUCCESS

                        await asyncio.sleep(2)

                        print(
                            "Verificando nuevamente "
                            "el estado de la página..."
                        )

                        blocked = (
                            await self.captcha_provider.is_blocked(
                                page
                            )
                        )
                        
                        print("estatus", blocked)

                        if blocked:

                            status = AccessStatus.BLOCKED

                            print(
                                "La página continúa "
                                "bloqueada."
                            )

                        else:

                            print(
                                "Página verificada. "
                                "Continuando con la extracción."
                            )

                    else:

                        print(
                            "CAPTCHA no encontrado. "
                            "Comprobando bloqueo..."
                        )

                        blocked = (
                            await self.captcha_provider.is_blocked(
                                page
                            )
                        )
                        
                        if blocked:

                            status = AccessStatus.BLOCKED

                            print(
                                "Bloqueo de DataDome detectado."
                            )

                        else:

                            print(
                                "CAPTCHA presente, pero no "
                                "se encontró el slider ni "
                                "un bloqueo."
                            )

                self._validate_access(status)

                data = await self.extractor.extract(
                    page
                )

                product = Product(**data)

                return ScrapingResult(
                    product=product,
                    access_status=status.value,
                    attempts=attempt + 1,
                )

            except (
                CaptchaDetectedError,
                AccessBlockedError,
                NavigationError,
            ) as error:

                print(
                    f"Error: {error}"
                )

                if not self.retry_policy.should_retry(
                    attempt + 1
                ):
                    return ScrapingResult(
                        product=None,
                        access_status="failed",
                        attempts=attempt + 1,
                        failure_reason=type(error).__name__,
                    )

                delay = self.retry_policy.get_delay(
                    attempt
                )

                print(
                    f"Reintentando en {delay} segundos..."
                )

                await asyncio.sleep(delay)

    def _validate_access(
        self,
        status: AccessStatus,
    ) -> None:

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