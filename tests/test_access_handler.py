from unittest.mock import AsyncMock

import pytest

from resilience.access_handler import AccessHandler
from resilience.access_result import (
    AccessBlocked,
    AccessGranted,
    CaptchaRequired,
)


@pytest.mark.asyncio
async def test_check_returns_access_when_no_captcha():
    access_detector = AsyncMock()
    access_detector.detect.return_value = AccessGranted()

    captcha_provider = AsyncMock()

    handler = AccessHandler(
        access_detector=access_detector,
        captcha_provider=captcha_provider,
    )

    page = AsyncMock()

    result = await handler.check(page)

    assert isinstance(result, AccessGranted)
    assert result.status == "success"

    captcha_provider.solve.assert_not_awaited()
    access_detector.detect.assert_awaited_once_with(page)


@pytest.mark.asyncio
async def test_check_solves_captcha_and_rechecks_access():
    access_detector = AsyncMock()
    access_detector.detect.side_effect = [
        CaptchaRequired(),
        AccessGranted(),
    ]

    captcha_provider = AsyncMock()
    captcha_provider.solve.return_value = True

    handler = AccessHandler(
        access_detector=access_detector,
        captcha_provider=captcha_provider,
    )

    page = AsyncMock()

    result = await handler.check(page)

    assert isinstance(result, AccessGranted)
    assert result.status == "success"

    captcha_provider.solve.assert_awaited_once_with(page)
    assert access_detector.detect.await_count == 2


@pytest.mark.asyncio
async def test_check_returns_access_status_when_captcha_cannot_be_solved():
    access_detector = AsyncMock()
    access_detector.detect.side_effect = [
        CaptchaRequired(),
        AccessBlocked(),
    ]

    captcha_provider = AsyncMock()
    captcha_provider.solve.return_value = False

    handler = AccessHandler(
        access_detector=access_detector,
        captcha_provider=captcha_provider,
    )

    page = AsyncMock()

    result = await handler.check(page)

    assert isinstance(result, AccessBlocked)
    assert result.status == "blocked"

    captcha_provider.solve.assert_awaited_once_with(page)
    assert access_detector.detect.await_count == 2


@pytest.mark.asyncio
async def test_check_revalidates_access_after_captcha():
    access_detector = AsyncMock()
    access_detector.detect.side_effect = [
        CaptchaRequired(),
        AccessGranted(),
    ]

    captcha_provider = AsyncMock()
    captcha_provider.solve.return_value = True

    handler = AccessHandler(
        access_detector=access_detector,
        captcha_provider=captcha_provider,
    )

    page = AsyncMock()

    result = await handler.check(page)

    assert result.status == "success"
    assert access_detector.detect.await_count == 2