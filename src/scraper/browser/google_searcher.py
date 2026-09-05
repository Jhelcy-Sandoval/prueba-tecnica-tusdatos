import asyncio
import random
from urllib.parse import urljoin, urlparse

from playwright.async_api import Page

from integrations.captcha.captcha_provider import CaptchaProvider


class GoogleSearcher:
    '''
    Gestiona la búsqueda de un dominio objetivo mediante
    Google y coordina la gestión de verificaciones CAPTCHA.
    '''

    def __init__(
        self,
        captcha_provider: CaptchaProvider,
    ):
        '''
        Inicializa el buscador con el proveedor encargado
        de gestionar las verificaciones CAPTCHA.
        '''

        self.captcha_provider = captcha_provider

    async def search(
        self,
        page: Page,
        query: str,
        target_url: str,
    ) -> str | None:
        '''
        Ejecuta una búsqueda en Google y obtiene la URL del
        resultado correspondiente al dominio objetivo.
        '''

        target_domain = urlparse(
            target_url
        ).netloc

        print(
            f"Buscando en Google: {query}"
        )

        await page.goto(
            "https://www.google.com",
            wait_until="domcontentloaded",
        )

        await asyncio.sleep(
            random.uniform(1.5, 2.5)
        )

        if not await self._handle_captcha(page):
            return None

        try:
            reject_or_accept_btn = page.locator(
                'button:has-text("Aceptar todo"), '
                'button:has-text("Accept all")'
            )

            if await reject_or_accept_btn.is_visible(
                timeout=3000
            ):
                await reject_or_accept_btn.click()

                await asyncio.sleep(1)

        except Exception as error:
            print(
                "No fue posible gestionar el "
                f"consentimiento de Google: {error}"
            )

        search_box = page.locator(
            'textarea[name="q"], input[name="q"]'
        ).first

        await search_box.click()

        for char in query:
            await search_box.type(
                char,
                delay=random.randint(80, 220),
            )

        await asyncio.sleep(
            random.uniform(0.5, 1.2)
        )

        await search_box.press("Enter")

        await page.wait_for_load_state(
            "domcontentloaded"
        )

        await asyncio.sleep(
            random.uniform(2.0, 3.5)
        )

        print(
            f"URL después de buscar: {page.url}"
        )

        print(
            f"Título: {await page.title()}"
        )

        # Comprobar CAPTCHA después de realizar la búsqueda.
        if not await self._handle_captcha(page):
            return None

        results = page.locator(
            "cite.tjvcx.GvPZzd.cHaqb"
        )

        count = await results.count()

        print(
            f"Resultados encontrados: {count}"
        )

        for index in range(count):

            result = results.nth(index)

            href = (
                await result.inner_text()
            ).strip()

            if not href:
                continue

            href = href.split(
                " ›",
                maxsplit=1,
            )[0].strip()

            if not href.startswith(
                ("http://", "https://")
            ):
                href = f"https://{href}"

            result_domain = urlparse(
                href
            ).netloc

            if (
                result_domain == target_domain
                or result_domain.endswith(
                    f".{target_domain}"
                )
            ):

                title_link = result.locator(
                    "xpath=ancestor::a[@href][1]"
                )

                if (
                    await title_link.locator("h3").count()
                    == 0
                ):
                    continue

                destination = (
                    await title_link.get_attribute(
                        "href"
                    )
                )

                if not destination:
                    continue

                print(
                    "Resultado objetivo encontrado."
                )

                return urljoin(
                    page.url,
                    destination,
                )

        print(
            "No se encontró un resultado "
            "para el dominio objetivo."
        )

        return None

    async def _handle_captcha(
        self,
        page: Page,
    ) -> bool:
        '''
        Detecta una verificación CAPTCHA y delega su gestión
        al proveedor configurado.
        '''

        if not await self.captcha_provider.is_blocked(
            page
        ):
            return True

        print(
            "CAPTCHA detectado en Google."
        )

        solved = await self.captcha_provider.solve(
            page
        )

        if not solved:
            print(
                "No se pudo resolver el CAPTCHA."
            )
            return False

        await asyncio.sleep(2)

        return not await self.captcha_provider.is_blocked(
            page
        )