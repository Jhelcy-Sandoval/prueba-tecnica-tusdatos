from resilience.retry_policy import RetryPolicy
from config.settings import Settings

def test_should_retry():
    policy = RetryPolicy(
        max_attempts=3,
        base_delay=2.0,
        manual_intervention_delay=30.0,
    )

    assert policy.should_retry(1) is True
    assert policy.should_retry(2) is True
    assert policy.should_retry(3) is False


def test_get_delay():
    policy = RetryPolicy(
        max_attempts=3,
        base_delay=2.0,
        manual_intervention_delay=30.0,
    )

    assert policy.get_delay(0) == 2.0
    assert policy.get_delay(1) == 4.0
    assert policy.get_delay(2) == 8.0


def test_get_manual_intervention_delay():
    policy = RetryPolicy(
        max_attempts=3,
        base_delay=2.0,
        manual_intervention_delay=30.0,
    )

    assert policy.get_manual_intervention_delay() == 30.0
    
def test_retry_policy_from_settings():
    settings = Settings()

    policy = RetryPolicy.from_settings(settings)

    assert policy.max_attempts == settings.max_attempts
    assert policy.base_delay == settings.base_delay
    assert (
        policy.manual_intervention_delay
        == settings.manual_intervention_delay
    )