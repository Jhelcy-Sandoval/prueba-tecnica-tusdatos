import asyncio
import shutil  # <--- IMPORTANTE: Para borrar carpetas físicamente del disco
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
        return self.settings.proxies

    def _get_current_proxy(self) -> str | None:
        proxies = self._get_proxies()
        if not proxies:
            return None
        return proxies[self.proxy_index]

    def _get_next_proxy(self) -> str | None:
        proxies = self._get_proxies()
        if not proxies:
            return None
        self.proxy_index = (self.proxy_index + 1) % len(proxies)
        return proxies[self.proxy_index]

    # --- NUEVA FUNCIÓN PARA OBTENER LA RUTA DEL PERFIL ---
    def _get_profile_path(self) -> Path:
        '''Genera un perfil único por cada proxy para evitar mezclar cookies'''
        return Path(f"playwright-brave-profile-{self.proxy_index}").resolve()

    async def start(
        self,
        headless: bool = False,
        use_proxy: bool = False,
    ) -> BrowserContext:
        
        # Ahora el perfil cambia dependiendo del proxy_index
        profile_path = self._get_profile_path()
        
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]

        launch_options = {
            "user_data_dir": str(profile_path),
            "headless": headless,
            "viewport": {"width": 1280, "height": 720},
            "locale": "es-419",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "args": launch_args,
        }

        if self.settings.browser == "brave":
            launch_options["executable_path"] = self.settings.browser_path

        if use_proxy:
            proxy = self._get_current_proxy()
            if proxy:
                parsed_proxy = urlparse(proxy)
                scheme = parsed_proxy.scheme if parsed_proxy.scheme else "http"
                
                launch_options["proxy"] = {
                    "server": f"{scheme}://{parsed_proxy.hostname}:{parsed_proxy.port}"
                }
                if parsed_proxy.username:
                    launch_options["proxy"]["username"] = parsed_proxy.username
                if parsed_proxy.password:
                    launch_options["proxy"]["password"] = parsed_proxy.password

                print("Lanzando navegador con proxy configurado.", proxy)
            else:
                print("No hay proxies configurados. Usando conexión directa.")
        else:
            print("Usando conexión directa.")

        self.context = await self.playwright.chromium.launch_persistent_context(**launch_options)

        self.context.on(
            "page",
            lambda page: asyncio.create_task(self._setup_page_protection(page)),
        )

        return self.context

    async def rotate_proxy(
        self,
        headless: bool = False,
    ) -> Page:
        print("\n[Rotate] Iniciando destrucción del contexto actual...")
        
        # Cambiamos tu antiguo "self.close()" por la nueva función que destruye de verdad
        await self.destroy_context()

        # Avanzamos al siguiente proxy antes de arrancar el nuevo contexto
        self._get_next_proxy()
        print(f"[Rotate] Cambiando a proxy índice: {self.proxy_index}")

        await asyncio.sleep(2) # Tiempo para que Windows libere los archivos de Brave

        context = await self.start(
            headless=headless,
            use_proxy=True,
        )

        self.page = await context.new_page()
        return self.page

    async def _setup_page_protection(self, page: Page) -> None:
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        async def block_telemetry(route):
            url = route.request.url.lower()
            if "cookie_consent/accept" in url or "newrelic" in url or "bam.nr-data.net" in url:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_telemetry)

    async def apply_stealth(self, page: Page) -> None:
        await self._setup_page_protection(page)

    async def close(self) -> None:
        # Redirigimos close a destroy_context para que siempre limpie a fondo
        await self.destroy_context()

    # --- TU FUNCIÓN CORREGIDA PARA ELIMINAR DE VERDAD ---
    async def destroy_context(self):
        '''
        Elimina por completo el contexto actual del navegador,
        libera recursos y BORRA las cookies viejas del disco duro.
        '''
        profile_a_borrar = self._get_profile_path()

        if self.page:
            try:
                await self.page.close()
            except Exception as error:
                print(f"No fue posible cerrar la página: {error}")
            finally:
                self.page = None

        if self.context:
            try:
                await self.context.close()
                print("Contexto de Playwright cerrado de forma lógica.")
            except Exception as error:
                print(f"No fue posible cerrar el contexto: {error}")
            finally:
                self.context = None

        # Esperar un instante corto a que los procesos de Brave se apaguen por completo
        await asyncio.sleep(1)

        # BORRADO FÍSICO: Eliminamos la carpeta del disco para borrar las cookies de DataDome
        if profile_a_borrar.exists():
            try:
                shutil.rmtree(profile_a_borrar)
                print(f"Éxito: Carpeta de cookies eliminada físicamente: {profile_a_borrar.name}")
            except Exception as e:
                print(f"Advertencia: Windows bloqueó temporalmente el borrado de la carpeta: {e}")
