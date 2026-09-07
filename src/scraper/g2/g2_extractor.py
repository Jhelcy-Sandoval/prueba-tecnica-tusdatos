from playwright.async_api import Page

from config.settings import Settings
from scraper.g2.g2_product_extractor import G2ProductExtractor
from scraper.g2.g2_selector_resolver import G2SelectorResolver
from scraper.g2.g2_selectors import G2Selectors
from scraper.g2.g2_ui_handler import G2UIHandler


class G2Extractor:
    '''
    Coordina la extracción de productos desde los resultados
    de búsqueda de G2.
    '''

    def __init__(
        self,
        ui_handler: G2UIHandler,
        product_extractor: G2ProductExtractor,
        selector_resolver: G2SelectorResolver,
        settings: Settings,
    ):
        '''
        Inicializa el extractor con los componentes encargados
        de la interfaz, la extracción individual de productos,
        la resolución de selectores y la configuración del scraper.
        '''

        self.ui_handler = ui_handler
        self.product_extractor = product_extractor
        self.selector_resolver = selector_resolver
        self.settings = settings

    async def extract(
        self,
        page: Page,
    ) -> dict:
        '''
        Obtiene los candidatos disponibles en los resultados
        de G2 y coordina la extracción de cada producto.
        '''

        await self.ui_handler.dismiss_login_overlay(
            page
        )

        candidates = await self._get_candidates(
            page
        )

        products = []

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            print(
                f"\n=== PRODUCTO {index} ==="
            )

            product = await self.product_extractor.extract(
                page,
                candidate,
            )

            if product:
                products.append(product)

        if not products:
            return {
                "search_success": False,
                "message": "No se encontraron productos.",
                "products": [],
            }

        return {
            "search_success": True,
            "message": "Productos extraídos correctamente.",
            "products": products,
        }

    async def _get_candidates(
        self,
        page: Page,
    ) -> list[dict]:
        '''
        Obtiene y normaliza los candidatos de productos
        encontrados en los resultados de G2.
        '''

        links = await self.selector_resolver.find_all(
            page,
            G2Selectors.PRODUCT,
        )

        if links is None:
            print(
                "No se encontraron links de productos."
            )
            return []

        count = await links.count()

        print(
            f"Links candidatos: {count}"
        )

        candidates = []
        seen_urls = set()

        for index in range(count):
            link = links.nth(index)

            name = (
                await link.inner_text()
            ).strip()

            href = await link.get_attribute(
                "href"
            )

            if not name or not href:
                continue

            if href.startswith("/"):
                href = (
                    f"https://www.g2.com{href}"
                )

            if href in seen_urls:
                continue

            seen_urls.add(href)

            candidates.append(
                {
                    "name": name,
                    "url": href,
                }
            )

            if len(candidates) >= self.settings.max_products:
                break

        return candidates