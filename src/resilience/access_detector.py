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

    CAPTCHA_SELECTOR = 'iframe[title="DataDome CAPTCHA"]'
    HARD_BLOCK_SELECTOR = '[data-dd-response-page="hard-block"]'

    async def detect(
        self,
        page: Page,
    ) -> AccessResult:
        '''
        Analiza el contenido de la página y sus iframes para
        determinar si el acceso fue concedido, bloqueado o
        requiere una verificación CAPTCHA.
        '''

        try:
            for frame in page.frames:
                try:
                    content = (
                        await frame.content()
                    ).lower()

                except Exception:
                    continue

                if (
                    'data-dd-response-page="hard-block"' in content
                    or "dd-response-page--hard-block" in content
                ):
                    print(
                        "Hard-block de DataDome detectado."
                    )

                    return AccessBlocked()

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
            "access denied" in content
            or "access blocked" in content
        ):
            return AccessBlocked()

        if (
            "datadome" in content
            or "captcha-delivery.com" in content
        ):
            return CaptchaRequired()

        return AccessGranted()