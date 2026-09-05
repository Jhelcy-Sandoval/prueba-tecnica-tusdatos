from unittest.mock import AsyncMock, MagicMock

import pytest

from config.settings import Settings
from resilience.access_result import AccessGranted
from scraper.g2.g2_scraper import G2Scraper
from validation.scraping_result import ScrapingResult


@pytest.mark.asyncio
async def test_g2_scraper_success():
    settings = Settings(
        target_url="https://www.g2.com",
        search_query="software metrics",
    )

    scraper = G2Scraper(settings)

    scraper.g2_searcher.search = AsyncMock(return_value=True)

    scraper.access_handler.check = AsyncMock(
        return_value=AccessGranted()
    )

    scraper.extractor.extract = AsyncMock(
        return_value={
            "search_success": True,
            "message": "Productos extraídos correctamente.",
            "products": [
                {
                    "name": "Metric.ai",
                    "url": "https://www.g2.com/products/metric-ai/reviews",
                    "rating": 4.8,
                    "reviews": 100,
                }
            ],
        }
    )

    page = MagicMock()
    page.goto = AsyncMock()

    result = await scraper.scrape(
        page,
        "https://www.g2.com",
    )

    assert isinstance(result, ScrapingResult)
    assert result.access_status == "success"
    assert result.attempts == 1

    assert len(result.products) == 1
    assert result.products[0].product_name == "Metric.ai"
    assert str(result.products[0].product_url) == (
        "https://www.g2.com/products/metric-ai/reviews"
    )
    assert result.products[0].rating == 4.8
    assert result.products[0].reviews == 100


@pytest.mark.asyncio
async def test_g2_scraper_retries_after_navigation_error():
    settings = Settings(
        target_url="https://www.g2.com",
        search_query="software metrics",
        max_attempts=2,
        base_delay=0,
    )

    scraper = G2Scraper(settings)

    scraper.g2_searcher.search = AsyncMock(
        side_effect=[
            False,
            True,
        ]
    )

    scraper.access_handler.check = AsyncMock(
        return_value=AccessGranted()
    )

    scraper.extractor.extract = AsyncMock(
        return_value={
            "search_success": True,
            "message": "Productos extraídos correctamente.",
            "products": [
                {
                    "name": "Metric.ai",
                    "url": "https://www.g2.com/products/metric-ai/reviews",
                    "rating": 4.8,
                    "reviews": 100,
                }
            ],
        }
    )

    page = MagicMock()
    page.goto = AsyncMock()

    result = await scraper.scrape(
        page,
        "https://www.g2.com",
    )

    assert result.access_status == "success"
    assert result.attempts == 2
    assert len(result.products) == 1

    assert scraper.g2_searcher.search.await_count == 2


@pytest.mark.asyncio
async def test_g2_scraper_returns_failure_after_max_attempts():
    settings = Settings(
        target_url="https://www.g2.com",
        search_query="software metrics",
        max_attempts=2,
        base_delay=0,
    )

    scraper = G2Scraper(settings)

    scraper.g2_searcher.search = AsyncMock(
        return_value=False
    )

    scraper.access_handler.check = AsyncMock(
        return_value=AccessGranted()
    )

    page = MagicMock()
    page.goto = AsyncMock()

    result = await scraper.scrape(
        page,
        "https://www.g2.com",
    )

    assert result.access_status == "failed"
    assert result.attempts == 2
    assert result.products == []
    assert result.failure_reason == "NavigationError"

    assert scraper.g2_searcher.search.await_count == 2