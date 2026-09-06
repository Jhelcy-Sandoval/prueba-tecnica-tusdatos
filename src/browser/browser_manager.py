import asyncio
from urllib.parse import urlparse
from pathlib import Path

from playwright.async_api import (
    BrowserContext,
    Page,
    Playwright,
)

from config.settings import Settings


class BrowserManager:
    '''
    Gestiona el navegador y los contextos persistentes utilizados
    durante la ejecución del scraper.
    '''

    def __init__(
        self,
        playwright: Playwright,
        settings: Settings,
    ):
        self.playwright = playwright
        self.settings = settings
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.proxy_index = 0

    def _get_proxies(self) -> list[str]:
        '''
        Obtiene los proxies configurados en Settings.
        '''
        return self.settings.proxies

    def _get_current_proxy(self) -> str | None:
        '''
        Obtiene el proxy correspondiente a la posición actual.
        '''
        proxies = self._get_proxies()

        if not proxies:
            return None

        return proxies[self.proxy_index]

    def _get_next_proxy(self) -> str | None:
        '''
        Obtiene el siguiente proxy disponible.
        '''
        proxies = self._get_proxies()

        if not proxies:
            return None

        self.proxy_index = (self.proxy_index + 1) % len(proxies)

        return proxies[self.proxy_index]

    async def start(
        self,
        headless: bool = False,
        use_proxy: bool = False,
    ) -> BrowserContext:
        '''
        Inicia un contexto persistente del navegador con
        la configuración definida en Settings.
        '''

        profile_path = Path(
            "playwright-brave-profile"
        ).resolve()
        
        # Configuración de argumentos nativos indispensables para evadir DataDome.
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
            launch_options["executable_path"] = (
                self.settings.browser_path
            )

        if use_proxy:
            proxy = self._get_current_proxy()

            if proxy:
                parsed_proxy = urlparse(proxy)

                launch_options["proxy"] = {
                    "server": (
                        f"{parsed_proxy.scheme}://"
                        f"{parsed_proxy.hostname}:{parsed_proxy.port}"
                    ),
                    "username": parsed_proxy.username,
                    "password": parsed_proxy.password,
                }

                print(
                    "Lanzando navegador con proxy configurado."
                )
            else:
                print(
                    "No hay proxies configurados. "
                    "Usando conexión directa."
                )
        else:
            print(
                "Usando conexión directa."
            )

        self.context = (
            await self.playwright.chromium
            .launch_persistent_context(
                **launch_options
            )
        )

        self.context.on(
            "page",
            lambda page: asyncio.create_task(
                self._setup_page_protection(page)
            ),
        )

        return self.context

    async def rotate_proxy(
        self,
        headless: bool = False,
    ) -> Page:
        '''
        Cambia al siguiente proxy y crea un nuevo contexto
        de navegador.
        '''

        self._get_next_proxy()

        print(
            "\nCambiando de entorno. "
            "Usando el siguiente proxy."
        )

        await self.close()

        await asyncio.sleep(1.5)

        context = await self.start(
            headless=headless,
            use_proxy=True,
        )

        self.page = await context.new_page()

        return self.page

    async def _setup_page_protection(
        self,
        page: Page,
    ) -> None:
        '''
        Configura las reglas de inicialización y protección
        de la página.
        '''

        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
        )

        async def block_telemetry(route):
            url = route.request.url.lower()

            if (
                "cookie_consent/accept" in url
                or "newrelic" in url
                or "bam.nr-data.net" in url
            ):
                await route.abort()
            else:
                await route.continue_()

        await page.route(
            "**/*",
            block_telemetry,
        )

    async def apply_stealth(
        self,
        page: Page,
    ) -> None:
        '''
        Aplica la configuración de protección a una página.
        '''

        await self._setup_page_protection(page)

    async def close(self) -> None:
        '''
        Cierra el contexto actual del navegador.
        '''

        if self.context:
            await self.context.close()
            self.context = None