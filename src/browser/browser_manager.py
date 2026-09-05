import asyncio
from pathlib import Path

from playwright.async_api import (
    BrowserContext,
    Page,
    Playwright,
)

from config.settings import Settings


class BrowserManager:

    def __init__(
        self,
        playwright: Playwright,
        settings: Settings,
    ):
        self.playwright = playwright
        self.settings = settings
        self.context: BrowserContext | None = None

    async def start(
        self,
        headless: bool = False,
    ) -> BrowserContext:
        '''
        Inicia el navegador configurado y establece el contexto
        de navegación con los parámetros definidos en Settings.
        '''

        profile_path = Path("playwright-brave-profile").resolve()

        # Configuración de argumentos nativos para el navegador.
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]

        launch_options = {
            "user_data_dir": str(profile_path),
            "headless": headless,
            "viewport": {
                "width": 1280,
                "height": 720,
            },
            "locale": "es-419",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "args": launch_args,
        }

        if self.settings.browser == "brave":
            launch_options["executable_path"] = self.settings.browser_path

        self.context = await self.playwright.chromium.launch_persistent_context(
            **launch_options,
        )

        self.context.on(
            "page",
            lambda page: asyncio.create_task(
                self._setup_page_protection(page)
            ),
        )

        return self.context

    async def _setup_page_protection(self, page: Page) -> None:
        '''
        Configura los scripts de inicialización y las reglas
        de navegación aplicadas a las páginas del navegador.
        '''

        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        async def block_telemetry(route):
            # Filtrar solicitudes de telemetría que no son necesarias.
            url = route.request.url.lower()

            if (
                "cookie_consent/accept" in url
                or "newrelic" in url
                or "bam.nr-data.net" in url
            ):
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_telemetry)

    async def apply_stealth(
        self,
        page: Page,
    ) -> None:
        '''
        Aplica la configuración de protección a una página
        existente del contexto del navegador.
        '''

        await self._setup_page_protection(page)

    async def close(self) -> None:
        '''
        Cierra el contexto del navegador y libera los recursos
        utilizados durante la ejecución.
        '''

        if self.context:
            await self.context.close()
            self.context = None