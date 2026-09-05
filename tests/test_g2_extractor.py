from unittest.mock import AsyncMock, MagicMock

import pytest

from resilience.access_result import AccessGranted
from scraper.g2.g2_extractor import G2Extractor


@pytest.mark.asyncio
async def test_extract_returns_products():
    page = MagicMock()

    ui_handler = AsyncMock()
    access_handler = AsyncMock()

    access_handler.check.return_value = AccessGranted()

    links = MagicMock()
    links.count = AsyncMock(return_value=1)
    links.nth.return_value.inner_text = AsyncMock(
        return_value="Metric.ai"
    )
    links.nth.return_value.get_attribute = AsyncMock(
        return_value="/products/metric-ai/reviews"
    )

    page.locator.return_value = links

    product_page = AsyncMock()
    product_page.url = (
        "https://www.g2.com/products/metric-ai/reviews"
    )
    product_page.title = AsyncMock(
        return_value="Metric.ai Reviews"
    )

    page.context.new_page = AsyncMock(
        return_value=product_page
    )

    extractor = G2Extractor(
        ui_handler=ui_handler,
        access_handler=access_handler,
    )

    extractor._extract_product_info = AsyncMock(
        return_value={
            "rating": 4.8,
            "reviews": 100,
        }
    )

    result = await extractor.extract(page)

    assert result["search_success"] is True
    assert len(result["products"]) == 1
    assert result["products"][0]["name"] == "Metric.ai"
    assert result["products"][0]["rating"] == 4.8
    assert result["products"][0]["reviews"] == 100


@pytest.mark.asyncio
async def test_extract_returns_failure_when_no_products():
    page = MagicMock()

    ui_handler = AsyncMock()
    access_handler = AsyncMock()

    links = MagicMock()
    links.count = AsyncMock(return_value=0)

    page.locator.return_value = links

    extractor = G2Extractor(
        ui_handler=ui_handler,
        access_handler=access_handler,
    )

    result = await extractor.extract(page)

    assert result["search_success"] is False
    assert result["products"] == []
    assert result["message"] == "No se encontraron productos."


@pytest.mark.asyncio
async def test_extract_removes_duplicate_urls():
    page = MagicMock()

    ui_handler = AsyncMock()
    access_handler = AsyncMock()

    access_handler.check.return_value = AccessGranted()

    links = MagicMock()
    links.count = AsyncMock(return_value=2)

    first_link = MagicMock()
    first_link.inner_text = AsyncMock(
        return_value="Metric.ai"
    )
    first_link.get_attribute = AsyncMock(
        return_value="/products/metric-ai/reviews"
    )

    second_link = MagicMock()
    second_link.inner_text = AsyncMock(
        return_value="Metric.ai"
    )
    second_link.get_attribute = AsyncMock(
        return_value="/products/metric-ai/reviews"
    )

    links.nth.side_effect = [
        first_link,
        second_link,
    ]

    page.locator.return_value = links

    product_page = AsyncMock()
    product_page.url = (
        "https://www.g2.com/products/metric-ai/reviews"
    )
    product_page.title = AsyncMock(
        return_value="Metric.ai Reviews"
    )

    page.context.new_page = AsyncMock(
        return_value=product_page
    )

    extractor = G2Extractor(
        ui_handler=ui_handler,
        access_handler=access_handler,
    )

    extractor._extract_product_info = AsyncMock(
        return_value={
            "rating": 4.8,
            "reviews": 100,
        }
    )

    result = await extractor.extract(page)

    assert result["search_success"] is True
    assert len(result["products"]) == 1


@pytest.mark.asyncio
async def test_extract_dismisses_login_overlay():
    page = MagicMock()

    ui_handler = AsyncMock()
    access_handler = AsyncMock()

    links = MagicMock()
    links.count = AsyncMock(return_value=0)

    page.locator.return_value = links

    extractor = G2Extractor(
        ui_handler=ui_handler,
        access_handler=access_handler,
    )

    await extractor.extract(page)

    ui_handler.dismiss_login_overlay.assert_awaited_once_with(
        page
    )