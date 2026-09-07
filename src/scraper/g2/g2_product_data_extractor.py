from playwright.async_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from scraper.g2.g2_selector_resolver import G2SelectorResolver
from scraper.g2.g2_selectors import G2Selectors


class G2ProductDataExtractor:
    '''
    Extrae y transforma los datos disponibles
    de un producto individual de G2.
    '''

    def __init__(
        self,
        selector_resolver: G2SelectorResolver,
    ):
        '''
        Inicializa el extractor con el componente
        encargado de resolver los selectores.
        '''

        self.selector_resolver = selector_resolver

    async def extract(
        self,
        page: Page,
    ) -> dict:
        '''
        Extrae el rating y el número de reviews
        de un producto de G2.
        '''

        rating = None
        reviews = None

        rating_locator = await self.selector_resolver.find_first(
            page,
            G2Selectors.RATING,
        )

        if rating_locator:
            try:
                rating_text = (
                    await rating_locator.inner_text()
                ).strip()

                print(
                    "Rating encontrado:",
                    rating_text,
                )

                rating = self._parse_rating(
                    rating_text.split("/")[0]
                )

            except PlaywrightTimeoutError:
                print(
                    "Rating no encontrado "
                    "(timeout esperando el elemento)."
                )

        reviews_locator = await self.selector_resolver.find_first(
            page,
            G2Selectors.REVIEWS,
        )

        if reviews_locator:
            try:
                reviews_text = (
                    await reviews_locator.inner_text()
                ).strip()

                print(
                    "Reviews encontrado:",
                    reviews_text,
                )

                reviews = self._parse_reviews(
                    reviews_text
                )

            except PlaywrightTimeoutError:
                print(
                    "Reviews no encontrado "
                    "(timeout esperando el elemento)."
                )

        return {
            "rating": rating,
            "reviews": reviews,
        }

    @staticmethod
    def _parse_rating(
        value: str,
    ) -> float | None:
        '''
        Convierte un valor de rating en formato de texto
        a un número decimal.
        '''

        try:
            return float(
                value.replace(",", ".").strip()
            )

        except (
            ValueError,
            AttributeError,
        ):
            return None

    @staticmethod
    def _parse_reviews(
        value: str,
    ) -> int | None:
        '''
        Convierte la cantidad de reviews desde texto a entero,
        eliminando caracteres de formato como paréntesis
        y separadores.
        '''

        try:
            cleaned = (
                value
                .replace("(", "")
                .replace(")", "")
                .replace(",", "")
                .replace(".", "")
                .strip()
            )

            return int(cleaned)

        except (
            ValueError,
            AttributeError,
        ):
            return None