import asyncio

from playwright.async_api import Page

from browser.browser_manager import BrowserManager
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
from scraper.g2.g2_product_data_extractor import (
    G2ProductDataExtractor,
)
from scraper.g2.g2_product_extractor import G2ProductExtractor
from scraper.g2.g2_product_validator import G2ProductValidator
from scraper.g2.g2_searcher import G2Searcher
from scraper.g2.g2_selector_resolver import G2SelectorResolver
from scraper.g2.g2_ui_handler import G2UIHandler
from validation.product import Product
from validation.scraping_result import ScrapingResult


class G2Scraper(BaseScraper):
    '''
    Ejecuta el proceso de extracción de información de G2
    aplicando validación de acceso, CAPTCHA, reintentos y
    rotación de proxy ante bloqueos.
    '''

    def __init__(
        self,
        settings: Settings,
    ):
        '''
        Inicializa las dependencias necesarias para realizar
        el proceso de scraping de G2.
        '''

        self.retry_policy = RetryPolicy.from_settings(
            settings
        )

        self.access_detector = AccessDetector()

        selector_resolver = G2SelectorResolver()
        
        g2_captcha_provider = G2CaptchaProvider(
            selector_resolver=selector_resolver,
        )

        self.access_handler = AccessHandler(
            access_detector=self.access_detector,
            captcha_provider=g2_captcha_provider,
        )


        self.g2_searcher = G2Searcher(
            search_query=settings.g2_search_query,
            selector_resolver=selector_resolver,
        )

        ui_handler = G2UIHandler()

        product_validator = G2ProductValidator()

        data_extractor = G2ProductDataExtractor(
            selector_resolver=selector_resolver,
        )

        product_extractor = G2ProductExtractor(
            access_handler=self.access_handler,
            product_validator=product_validator,
            data_extractor=data_extractor,
        )

        self.extractor = G2Extractor(
            ui_handler=ui_handler,
            product_extractor=product_extractor,
            selector_resolver=selector_resolver,
            settings=settings,
        )

    async def scrape(
        self,
        page: Page,
        url: str,
        browser_manager: BrowserManager,
    ) -> ScrapingResult:
        '''
        Ejecuta una extracción de G2 y utiliza un nuevo proxy
        cuando el acceso actual es bloqueado.
        '''

        current_page = page

        for attempt in range(
            self.retry_policy.max_attempts
        ):
            try:
                print(
                    f"Intento {attempt + 1}/"
                    f"{self.retry_policy.max_attempts}"
                )

                await current_page.goto(
                    url,
                    wait_until="domcontentloaded",
                )

                access = await self.access_handler.check(
                    current_page
                )

                access.validate()

                search_success = await self.g2_searcher.search(
                    current_page
                )

                if not search_success:
                    raise NavigationError(
                        "No fue posible realizar "
                        "la búsqueda en G2."
                    )

                access = await self.access_handler.check(
                    current_page
                )

                access.validate()

                data = await self.extractor.extract(
                    current_page
                )

                if not data.get("search_success"):
                    raise NavigationError(
                        "No se encontraron productos en G2."
                    )

                products = [
                    Product(
                        product_name=item["name"],
                        product_url=item["url"],
                        rating=item["rating"],
                        reviews=item["reviews"],
                    )
                    for item in data["products"]
                ]

                print(data["message"])
                print("Productos encontrados:")

                for product in products:
                    print(
                        f"- {product.product_name}"
                    )

                return ScrapingResult(
                    products=products,
                    access_status=access.status,
                    attempts=attempt + 1,
                )

            except CaptchaDetectedError as error:
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
                        failure_reason=type(error).__name__,
                    )

                delay = self.retry_policy.get_delay(
                    attempt
                )

                print(
                    f"Reintentando en {delay} segundos..."
                )

                await asyncio.sleep(delay)

            except AccessBlockedError as error:
                print(
                    f"Acceso bloqueado: {error}"
                )

                if not self.retry_policy.should_retry(
                    attempt + 1
                ):
                    return ScrapingResult(
                        products=[],
                        access_status="failed",
                        attempts=attempt + 1,
                        failure_reason=type(error).__name__,
                    )

                print(
                    "El acceso actual está bloqueado."
                )

                print(
                    "Intentando utilizar el siguiente proxy..."
                )

                current_page = await browser_manager.rotate_proxy(
                    headless=browser_manager.settings.headless
                )

            except NavigationError as error:
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
                        failure_reason=type(error).__name__,
                    )

                delay = self.retry_policy.get_delay(
                    attempt
                )

                print(
                    f"Reintentando en {delay} segundos..."
                )

                await asyncio.sleep(delay)

        return ScrapingResult(
            products=[],
            access_status="failed",
            attempts=self.retry_policy.max_attempts,
            failure_reason="MaxAttemptsExceeded",
        )