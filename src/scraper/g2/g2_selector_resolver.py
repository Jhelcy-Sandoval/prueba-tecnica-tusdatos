from playwright.async_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
)


class G2SelectorResolver:
    '''
    Resuelve elementos de G2 utilizando una lista ordenada
    de selectores alternativos.
    '''

    async def find_first(
        self,
        page: Page,
        selectors: list[str],
        timeout: int = 6000,
    ):
        '''
        Busca el primer elemento disponible utilizando
        los selectores proporcionados.
        '''

        for selector in selectors:
            locator = page.locator(
                selector
            ).first

            try:
                await locator.wait_for(
                    state="attached",
                    timeout=timeout,
                )

                print(
                    f"Selector encontrado: {selector}"
                )

                return locator

            except PlaywrightTimeoutError:
                print(
                    f"Selector no encontrado: {selector}"
                )

        return None

    async def find_all(
        self,
        page: Page,
        selectors: list[str],
        timeout: int = 6000,
    ):
        '''
        Busca una colección de elementos utilizando
        una lista ordenada de selectores alternativos.
        '''

        for selector in selectors:
            locator = page.locator(
                selector
            )

            try:
                await locator.first.wait_for(
                    state="attached",
                    timeout=timeout,
                )

                print(
                    f"Selector encontrado: {selector}"
                )

                return locator

            except PlaywrightTimeoutError:
                print(
                    f"Selector no encontrado: {selector}"
                )

        return None