import pytest

from resilience.access_result import (
    AccessBlocked,
    AccessGranted,
    AccessUnknown,
    CaptchaRequired,
)
from resilience.exceptions import (
    AccessBlockedError,
    CaptchaDetectedError,
    NavigationError,
)


def test_access_granted():
    result = AccessGranted()

    assert result.status == "success"
    result.validate()


def test_captcha_required():
    result = CaptchaRequired()

    assert result.status == "captcha"

    with pytest.raises(CaptchaDetectedError):
        result.validate()


def test_access_blocked():
    result = AccessBlocked()

    assert result.status == "blocked"

    with pytest.raises(AccessBlockedError):
        result.validate()


def test_access_unknown():
    result = AccessUnknown()

    assert result.status == "unknown"

    with pytest.raises(NavigationError):
        result.validate()