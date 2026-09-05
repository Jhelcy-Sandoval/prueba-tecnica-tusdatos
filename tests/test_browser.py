from unittest.mock import AsyncMock, MagicMock

import pytest

from browser.browser_manager import BrowserManager


@pytest.mark.asyncio
async def test_browser_manager_starts_and_closes():
    playwright = MagicMock()

    context = MagicMock()
    context.close = AsyncMock()

    chromium = MagicMock()
    chromium.launch_persistent_context = AsyncMock(
        return_value=context
    )

    playwright.chromium = chromium

    browser_manager = BrowserManager(playwright)

    result = await browser_manager.start(headless=True)

    assert result is context
    assert browser_manager.context is context

    chromium.launch_persistent_context.assert_awaited_once()

    await browser_manager.close()

    context.close.assert_awaited_once()
    assert browser_manager.context is None