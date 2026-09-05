from unittest.mock import AsyncMock, MagicMock

import pytest

from scraper.browser.google_searcher import GoogleSearcher


@pytest.mark.asyncio
async def test_google_searcher_returns_target_url():
    page = MagicMock()

    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.title = AsyncMock(
        return_value="Google"
    )
    page.url = "https://www.google.com/search?q=Metric.ai"

    search_box = MagicMock()
    search_box.click = AsyncMock()
    search_box.type = AsyncMock()
    search_box.press = AsyncMock()

    def locator_side_effect(selector):
        if "button:has-text" in selector:
            consent_button = MagicMock()
            consent_button.is_visible = AsyncMock(
                return_value=False
            )
            return consent_button

        if "textarea[name" in selector:
            locator = MagicMock()
            locator.first = search_box
            return locator

        if "cite.tjvcx" in selector:
            title_link = MagicMock()

            h3 = MagicMock()
            h3.count = AsyncMock(
                return_value=1
            )

            title_link.locator.return_value = h3
            title_link.get_attribute = AsyncMock(
                return_value="https://www.g2.com/es"
            )

            result = MagicMock()
            result.inner_text = AsyncMock(
                return_value="https://www.g2.com"
            )
            result.locator.return_value = title_link

            results = MagicMock()
            results.count = AsyncMock(
                return_value=1
            )
            results.nth.return_value = result

            return results

        return MagicMock()

    page.locator.side_effect = locator_side_effect

    captcha_provider = AsyncMock()

    searcher = GoogleSearcher(
        captcha_provider=captcha_provider,
    )

    searcher._handle_captcha = AsyncMock(
        return_value=True,
    )

    result = await searcher.search(
        page,
        "Metric.ai",
        "https://www.g2.com/products/metric-ai/reviews",
    )

    assert result == "https://www.g2.com/es"

    searcher._handle_captcha.assert_awaited()


@pytest.mark.asyncio
async def test_google_searcher_returns_none_when_captcha_cannot_be_handled():
    page = MagicMock()
    page.goto = AsyncMock()

    captcha_provider = AsyncMock()

    searcher = GoogleSearcher(
        captcha_provider=captcha_provider,
    )

    searcher._handle_captcha = AsyncMock(
        return_value=False,
    )

    result = await searcher.search(
        page,
        "Metric.ai",
        "https://www.g2.com/products/metric-ai/reviews",
    )

    assert result is None

    searcher._handle_captcha.assert_awaited_once_with(page)


@pytest.mark.asyncio
async def test_google_searcher_handles_captcha():
    page = MagicMock()

    captcha_provider = AsyncMock()

    captcha_provider.is_blocked.side_effect = [
        True,
        False,
    ]

    captcha_provider.solve.return_value = True

    searcher = GoogleSearcher(
        captcha_provider=captcha_provider,
    )

    result = await searcher._handle_captcha(page)

    assert result is True

    captcha_provider.is_blocked.assert_awaited()

    captcha_provider.solve.assert_awaited_once_with(page)


@pytest.mark.asyncio
async def test_google_searcher_returns_false_when_captcha_solution_fails():
    page = MagicMock()

    captcha_provider = AsyncMock()

    captcha_provider.is_blocked.return_value = True
    captcha_provider.solve.return_value = False

    searcher = GoogleSearcher(
        captcha_provider=captcha_provider,
    )

    result = await searcher._handle_captcha(page)

    assert result is False

    captcha_provider.solve.assert_awaited_once_with(page)