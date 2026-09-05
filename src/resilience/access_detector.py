import asyncio

from playwright.async_api import Page

from resilience.access_result import (
    AccessBlocked,
    AccessGranted,
    AccessResult,
    CaptchaRequired,
)


class AccessDetector:
    '''
    Detecta el estado de acceso de una página durante
    el proceso de scraping.
    '''

    async def detect(
        self,
        page: Page,
    ) -> AccessResult:
        '''
        Analiza el contenido de la página para determinar
        si el acceso fue concedido, bloqueado o requiere
        una verificación CAPTCHA.
        '''

        try:
            content = (
                await page.content()
            ).lower()

        except Exception as error:
            print(
                "La página todavía está navegando. "
                f"Esperando antes de detectar acceso: {error}"
            )

            await asyncio.sleep(2)

            content = (
                await page.content()
            ).lower()

        if (
            "datadome" in content
            or "captcha-delivery.com" in content
        ):
            return CaptchaRequired()

        if (
            "access denied" in content
            or "access blocked" in content
        ):
            return AccessBlocked()

        return AccessGranted()