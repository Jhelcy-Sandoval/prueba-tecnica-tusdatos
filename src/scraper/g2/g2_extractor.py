from playwright.async_api import Page

from resilience.access_handler import AccessHandler
from resilience.exceptions import (
    AccessBlockedError,
    CaptchaDetectedError,
    NavigationError,
)
from scraper.g2.g2_ui_handler import G2UIHandler


class G2Extractor:
    '''
    Extrae información de productos desde los resultados
    de búsqueda de G2 y valida el acceso a sus páginas.
    '''

    PRODUCT_SELECTOR = 'a[href*="/products/"][href$="/reviews"]'
    MAX_PRODUCTS = 3

    def __init__(
        self,
        ui_handler: G2UIHandler,
        access_handler: AccessHandler,
    ):
        '''
        Inicializa el extractor con los componentes encargados
        de la interacción con la interfaz y la gestión del acceso.
        '''

        self.ui_handler = ui_handler
        self.access_handler = access_handler

    async def extract(self, page: Page) -> dict:
        '''
        Extrae los productos disponibles en los resultados de G2,
        accede a sus páginas y obtiene la información requerida.
        '''

        await self.ui_handler.dismiss_login_overlay(page)

        links = page.locator(self.PRODUCT_SELECTOR)
        count = await links.count()

        print(f"Links candidatos: {count}")

        candidates = []
        seen_urls = set()

        for index in range(count):
            link = links.nth(index)

            name = (await link.inner_text()).strip()
            href = await link.get_attribute("href")

            if not name or not href:
                continue

            if href.startswith("/"):
                href = f"https://www.g2.com{href}"

            if href in seen_urls:
                continue

            seen_urls.add(href)

            candidates.append(
                {
                    "name": name,
                    "url": href,
                }
            )

            if len(candidates) >= self.MAX_PRODUCTS:
                break

        products = []

        for index, candidate in enumerate(candidates, start=1):
            name = candidate["name"]
            href = candidate["url"]

            print(f"\n=== PRODUCTO {index} ===")
            print(f"Nombre: {name}")
            print(f"URL: {href}")

            product_page = await page.context.new_page()

            try:
                await product_page.goto(
                    href,
                    wait_until="domcontentloaded",
                )

                print(f"URL producto: {href}")
                print(f"Título: {await product_page.title()}")
                print(f"URL actual: {product_page.url}")
                print(f"Título: {await product_page.title()}")

                access = await self.access_handler.check(product_page)
                access.validate()

                current_url = product_page.url.lower()
                title = (await product_page.title()).lower()

                if "/products/" not in current_url:
                    print(
                        f"Página inesperada para '{name}'. "
                        f"URL actual: {product_page.url}"
                    )
                    continue

                expected_slug = (
                    href.rstrip("/")
                    .split("/")[-2]
                    .lower()
                )

                if expected_slug not in current_url:
                    print(
                        f"Advertencia: la URL no corresponde "
                        f"al producto '{name}'."
                    )
                    print(f"Esperada: {href}")
                    print(f"Actual: {product_page.url}")
                    continue

                product_data = await self._extract_product_info(
                    product_page
                )

                rating = product_data["rating"]
                reviews = product_data["reviews"]

                print(f"Rating encontrado: {rating}/5")
                print(f"Reviews encontrado: ({reviews})")

                products.append(
                    {
                        "name": name,
                        "url": href,
                        "rating": rating,
                        "reviews": reviews,
                    }
                )

                print("Producto guardado.")

            except (
                CaptchaDetectedError,
                AccessBlockedError,
                NavigationError,
            ):
                raise

            except Exception as error:
                print(
                    f"Error procesando '{name}': {error}"
                )

            finally:
                await product_page.close()
                print("Pestaña del producto cerrada.")

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

    async def _extract_product_info(
        self,
        page: Page,
    ) -> dict:
        '''
        Extrae el rating y la cantidad de reviews disponibles
        en la página de un producto.
        '''

        print(
            "URL actual:",
            page.url,
        )

        print(
            "Título:",
            await page.title(),
        )

        rating = None
        reviews = None

        rating_locator = page.locator(
            ".elv-star-wrapper__desc__rating"
        ).first

        if await rating_locator.count() > 0:

            rating_text = (
                await rating_locator.inner_text()
            ).strip()

            print(
                "Rating encontrado:",
                rating_text,
            )

            try:
                rating = float(
                    rating_text.split("/")[0]
                )

            except ValueError as error:
                print(
                    "No fue posible convertir "
                    f"el rating: {error}"
                )

        else:
            print(
                "Rating no encontrado."
            )

        reviews_locator = page.locator(
            ".elv-star-wrapper__desc__count"
        ).first

        if await reviews_locator.count() > 0:

            reviews_text = (
                await reviews_locator.inner_text()
            ).strip()

            print(
                "Reviews encontrado:",
                reviews_text,
            )

            # Cambio: usamos el parser existente
            # para soportar "(504)" y "(7,964)".
            reviews = self._parse_reviews(
                reviews_text
            )

        else:
            print(
                "Reviews no encontrado."
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
        eliminando caracteres de formato como paréntesis y separadores.
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