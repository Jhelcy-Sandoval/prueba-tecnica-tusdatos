import asyncio

from playwright.async_api import async_playwright

from browser.browser_manager import BrowserManager
from config.settings import Settings
from integrations.captcha.google_captcha_provider import (
    GoogleCaptchaProvider,
)
from scraper.browser.google_searcher import GoogleSearcher
from metrics.scraper_metrics import ScraperMetrics
from metrics.report_generator import ReportGenerator
from persistence.dataset_writer import DatasetWriter
from scraper.g2.g2_scraper import G2Scraper
from scraper.scraping_runner import ScrapingRunner

from scraper.g2.g2_selector_resolver import G2SelectorResolver


async def main():
    '''
    Inicializa los componentes del sistema y ejecuta
    el proceso completo de scraping y generación de métricas.
    '''

    settings = Settings()

    dataset_writer = DatasetWriter()
    metrics = ScraperMetrics()
    report_generator = ReportGenerator()

    last_sample_id = (
        dataset_writer.get_last_sample_id()
    )

    start_sample_id = (
        last_sample_id + 1
    )

    print(
        f"Continuando desde la muestra "
        f"{start_sample_id}"
    )

    async with async_playwright() as playwright:
        browser_manager = BrowserManager(
            playwright=playwright,
            settings=settings,
        )

        # Brave con perfil persistente
        context = await browser_manager.start(
            headless=settings.headless,
            use_proxy=False,
        )

        page = await context.new_page()

        browser_manager.page = page

        # Aplicar configuración de stealth
        await browser_manager.apply_stealth(
            page
        )

        scraper = G2Scraper(
            settings
        )

        google_captcha_provider = GoogleCaptchaProvider()

        selector_resolver = G2SelectorResolver()

        google_searcher = GoogleSearcher(
            captcha_provider=google_captcha_provider,
            selector_resolver=selector_resolver,
        )

        runner = ScrapingRunner(
            scraper=scraper,
            google_searcher=google_searcher,
            browser_manager=browser_manager,
            sample_count=settings.sample_count,
            sample_delay=settings.sample_delay,
        )

        # Inicio del flujo del scraper
        async for (
            sample_id,
            result,
            execution_time,
        ) in runner.run(
            page,
            settings.search_query,
            settings.target_url,
            start_sample_id=start_sample_id,
        ):
            print(
                f"\nProcesando resultados de la muestra "
                f"{sample_id}"
            )

            print(result)

            # Generar las métricas
            metrics.record(
                result,
                execution_time,
            )

            # Guardar los resultados del flujo del scraper
            dataset_writer.save(
                result,
                execution_time,
                sample_id,
            )

        print("\nMétricas:")
        print(
            metrics.summary()
        )

        # Generar reporte después de registrar todas las métricas
        report_generator.generate(
            metrics
        )

        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(main())