from unittest.mock import AsyncMock, MagicMock

import pytest

from scraper.g2.g2_searcher import G2Searcher


@pytest.mark.asyncio
async def test_search_returns_false_without_query():
    page = MagicMock()

    searcher = G2Searcher()

    result = await searcher.search(page)

    assert result is False


@pytest.mark.asyncio
async def test_search_returns_false_when_input_is_not_found():
    page = MagicMock()

    search_input = AsyncMock()
    search_input.count.return_value = 0

    page.locator.return_value.first = search_input

    searcher = G2Searcher(
        search_query="metricas"
    )

    result = await searcher.search(page)

    assert result is False


@pytest.mark.asyncio
async def test_search_returns_false_when_input_is_not_visible():
    page = MagicMock()

    search_input = AsyncMock()
    search_input.count.return_value = 1
    search_input.is_visible.return_value = False

    page.locator.return_value.first = search_input

    searcher = G2Searcher(
        search_query="metricas"
    )

    result = await searcher.search(page)

    assert result is False


@pytest.mark.asyncio
async def test_search_writes_query_and_submits():
    page = MagicMock()

    search_input = AsyncMock()
    search_input.count.return_value = 1
    search_input.is_visible.return_value = True

    page.locator.return_value.first = search_input

    searcher = G2Searcher(
        search_query="metricas"
    )

    searcher._submit_search = AsyncMock(
        return_value=True
    )

    result = await searcher.search(page)

    assert result is True

    search_input.click.assert_awaited_once()
    search_input.fill.assert_awaited_once_with(
        "metricas"
    )

    searcher._submit_search.assert_awaited_once_with(
        page
    )


@pytest.mark.asyncio
async def test_submit_search_returns_false_when_button_is_not_found():
    page = MagicMock()

    search_button = AsyncMock()
    search_button.count.return_value = 0

    page.locator.return_value.first = search_button

    searcher = G2Searcher(
        search_query="metricas"
    )

    result = await searcher._submit_search(page)

    assert result is False


@pytest.mark.asyncio
async def test_submit_search_clicks_button():
    page = MagicMock()
    page.url = "https://www.g2.com/search"
    page.title = AsyncMock(
        return_value="G2 Search"
    )

    search_button = AsyncMock()
    search_button.count.return_value = 1

    page.locator.return_value.first = search_button

    page.wait_for_load_state = AsyncMock()

    searcher = G2Searcher(
        search_query="metricas"
    )

    result = await searcher._submit_search(page)

    assert result is True

    search_button.click.assert_awaited_once()
    page.wait_for_load_state.assert_awaited_once_with(
        "domcontentloaded",
        timeout=10_000,
    )