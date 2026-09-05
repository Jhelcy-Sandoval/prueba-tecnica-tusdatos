import asyncio

from playwright.async_api import Page

from config.settings import Settings
from integrations.captcha.g2_captcha_provider import G2CaptchaProvider
from resilience.access_detector import AccessDetector
from resilience.access_handler import AccessHandler
from resilience.exceptions import (
    AccessBlockedError,
    CaptchaDetectedError,
    NavigationError,
)
from resilience.retry_policy import RetryPolicy
from scraper.base_scraper import BaseScraper
from scraper.g2.g2_extractor import G2Extractor
from scraper.g2.g2_searcher import G2Searcher
from scraper.g2.g2_ui_handler import G2UIHandler
from validation.product import Product
from validation.scraping_result import ScrapingResult


class G2Scraper(BaseScraper):
    '''
    Coordina el proceso de scraping de G2, incluyendo la
    navegación, validación de acceso, búsqueda, extracción
    de productos y manejo de reintentos.
    '''

    def __init__(self, settings: Settings):
        '''
        Inicializa el scraper con la configuración y los
        componentes necesarios para ejecutar el flujo.
        '''

        self.retry_policy = RetryPolicy.from_settings(
            settings
        )

        self.access_detector = AccessDetector()

        g2_captcha_provider = G2CaptchaProvider()

        self.access_handler = AccessHandler(
            access_detector=self.access_detector,
            captcha_provider=g2_captcha_provider,
        )

        self.g2_searcher = G2Searcher(
            search_query=settings.g2_search_query
        )

        ui_handler = G2UIHandler()

        self.extractor = G2Extractor(
            ui_handler=ui_handler,
            access_handler=self.access_handler,
        )

    async def scrape(
        self,
        page: Page,
        url: str,
    ) -> ScrapingResult:
        '''
        Ejecuta el proceso de scraping de G2 y retorna el
        resultado de la ejecución junto con su estado de acceso
        y cantidad de intentos realizados.
        '''

        for attempt in range(
            self.retry_policy.max_attempts
        ):

            try:

                print(
                    f"Intento {attempt + 1}/"
                    f"{self.retry_policy.max_attempts}"
                )

                # Navegación inicial
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                )

                # Validar acceso
                access = await self.access_handler.check(
                    page
                )

                access.validate()

                # Realizar búsqueda
                search_success = (
                    await self.g2_searcher.search(page)
                )

                if not search_success:
                    raise NavigationError(
                        "No fue posible realizar "
                        "la búsqueda en G2."
                    )

                # Validar acceso después de la búsqueda
                access = await self.access_handler.check(
                    page
                )

                access.validate()

                # Extraer productos
                data = await self.extractor.extract(
                    page
                )

                if not data.get("search_success"):
                    raise NavigationError(
                        "No se encontraron "
                        "productos en G2."
                    )

                # Convertir resultados a modelos
                products = [
                    Product(
                        product_name=item["name"],
                        product_url=item["url"],
                        rating=item["rating"],
                        reviews=item["reviews"],
                    )
                    for item in data["products"]
                ]

                print(
                    data["message"]
                )

                print(
                    "Productos encontrados:"
                )

                for product in products:
                    print(
                        f"- {product.product_name}"
                    )

                # Retornar resultado
                return ScrapingResult(
                    products=products,
                    access_status=access.status,
                    attempts=attempt + 1,
                )

            except (
                CaptchaDetectedError,
                AccessBlockedError,
                NavigationError,
            ) as error:

                print(
                    f"Error: {error}"
                )

                if not self.retry_policy.should_retry(
                    attempt + 1
                ):
                    return ScrapingResult(
                        products=[],
                        access_status="failed",
                        attempts=attempt + 1,
                        failure_reason=(
                            type(error).__name__
                        ),
                    )

                delay = (
                    self.retry_policy.get_delay(
                        attempt
                    )
                )

                print(
                    f"Reintentando en "
                    f"{delay} segundos..."
                )

                await asyncio.sleep(
                    delay
                )

        return ScrapingResult(
            products=[],
            access_status="failed",
            attempts=self.retry_policy.max_attempts,
            failure_reason="MaxAttemptsExceeded",
        )