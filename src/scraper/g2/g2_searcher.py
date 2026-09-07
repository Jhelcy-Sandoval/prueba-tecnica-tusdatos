import asyncio

from playwright.async_api import Page

from scraper.g2.g2_selector_resolver import G2SelectorResolver
from scraper.g2.g2_selectors import G2Selectors

class G2Searcher:
    '''
    Gestiona las búsquedas dentro de G2.
    '''

    def __init__(
        self,
        search_query: str | None = None,
        selector_resolver: G2SelectorResolver | None = None,
    ):
        '''
        Inicializa el buscador con el término de búsqueda configurado.
        '''

        self.search_query = search_query
        self.selector_resolver = (
            selector_resolver
            or G2SelectorResolver()
        )

    async def search(self, page: Page) -> bool:
        '''
        Ejecuta una búsqueda en G2 utilizando el término configurado.
        '''

        if not self.search_query:
            return False

        search_input = await self.selector_resolver.find_first(
            page,
            G2Selectors.SEARCH_INPUT,
        )

        if search_input is None:
            print("Buscador de G2 no encontrado.")
            return False

        await search_input.click()
        await search_input.fill(self.search_query)

        print(
            f"Consulta escrita: {self.search_query}"
        )

        await asyncio.sleep(2)

        return await self._submit_search(page)

    async def _submit_search(
        self,
        page: Page,
    ) -> bool:
        '''
        Envía la consulta y espera la carga de los resultados
        de búsqueda.
        '''

        search_button = await self.selector_resolver.find_first(
            page,
            G2Selectors.SEARCH_BUTTON,
        )

        if search_button is None:
            print("Botón de búsqueda no encontrado.")
            return False

        print("Botón de búsqueda encontrado.")
        print("Enviando búsqueda...")

        await search_button.click()

        try:
            await page.wait_for_load_state(
                "domcontentloaded",
                timeout=10_000,
            )

        except Exception as error:
            print(
                f"No se pudo esperar la carga después "
                f"de la búsqueda: {error}"
            )

        await asyncio.sleep(3)

        print("URL:", page.url)
        print("Título:", await page.title())

        return True