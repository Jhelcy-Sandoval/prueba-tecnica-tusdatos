from playwright.async_api import Page

from resilience.access_handler import AccessHandler
from resilience.exceptions import (
    AccessBlockedError,
    CaptchaDetectedError,
    NavigationError,
)
from scraper.g2.g2_product_data_extractor import (
    G2ProductDataExtractor,
)
from scraper.g2.g2_product_validator import G2ProductValidator


class G2ProductExtractor:
    '''
    Extrae información de un producto individual
    desde una página de G2.
    '''

    def __init__(
        self,
        access_handler: AccessHandler,
        product_validator: G2ProductValidator,
        data_extractor: G2ProductDataExtractor,
    ):
        '''
        Inicializa el extractor con los componentes encargados
        de la gestión del acceso, validación del producto
        y extracción de datos.
        '''

        self.access_handler = access_handler
        self.product_validator = product_validator
        self.data_extractor = data_extractor

    async def extract(
        self,
        page: Page,
        candidate: dict,
    ) -> dict | None:
        '''
        Abre la página de un producto, valida el acceso,
        valida la URL y extrae la información del producto.
        '''

        name = candidate["name"]
        href = candidate["url"]

        print(f"Nombre: {name}")
        print(f"URL: {href}")

        product_page = await page.context.new_page()

        try:
            await product_page.goto(
                href,
                wait_until="domcontentloaded",
            )

            print(
                f"URL producto: {href}"
            )
            print(
                f"Título: {await product_page.title()}"
            )
            print(
                f"URL actual: {product_page.url}"
            )

            access = await self.access_handler.check(
                product_page
            )

            access.validate()

            if not self.product_validator.validate_url(
                href,
                product_page.url,
                name,
            ):
                return None

            product_data = await self.data_extractor.extract(
                product_page
            )

            return {
                "name": name,
                "url": href,
                "rating": product_data["rating"],
                "reviews": product_data["reviews"],
            }

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
            return None

        finally:
            await product_page.close()

            print(
                "Pestaña del producto cerrada."
            )