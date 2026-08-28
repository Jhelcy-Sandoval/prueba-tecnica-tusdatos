from resilience.retry_policy import RetryPolicy


def test_should_retry():
    policy = RetryPolicy(max_attempts=3)

    assert policy.should_retry(1) is True
    assert policy.should_retry(2) is True
    assert policy.should_retry(3) is False


def test_get_delay():
    policy = RetryPolicy(base_delay=2.0)

    assert policy.get_delay(0) == 2.0
    assert policy.get_delay(1) == 4.0
    assert policy.get_delay(2) == 8.0