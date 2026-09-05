import asyncio

from playwright.async_api import Page

from integrations.captcha.captcha_provider import CaptchaProvider
from resilience.access_detector import AccessDetector
from resilience.access_result import AccessResult


class AccessHandler:
    '''
    Gestiona el estado de acceso detectado en una página
    y coordina la gestión de verificaciones CAPTCHA.
    '''

    def __init__(
        self,
        access_detector: AccessDetector,
        captcha_provider: CaptchaProvider,
    ):
        '''
        Inicializa el manejador con el detector de acceso
        y el proveedor de CAPTCHA.
        '''

        self.access_detector = access_detector
        self.captcha_provider = captcha_provider

    async def check(
        self,
        page: Page,
    ) -> AccessResult:
        '''
        Comprueba el estado de acceso de la página y,
        cuando es necesario, gestiona el CAPTCHA antes
        de volver a verificar el acceso.
        '''

        access = await self.access_detector.detect(
            page
        )

        if access.status != "captcha":
            return access

        print(
            "CAPTCHA detectado."
        )

        solved = await self.captcha_provider.solve(
            page
        )

        if not solved:
            print(
                "No se pudo gestionar el CAPTCHA."
            )

            return await self.access_detector.detect(
                page
            )

        print(
            "CAPTCHA gestionado. "
            "Esperando navegación..."
        )

        try:
            await page.wait_for_load_state(
                "domcontentloaded",
                timeout=15_000,
            )
        except Exception as error:
            print(
                "No fue posible esperar "
                f"la navegación: {error}"
            )

        await asyncio.sleep(3)

        print(
            "Verificando nuevamente el acceso..."
        )

        return await self.access_detector.detect(
            page
        )