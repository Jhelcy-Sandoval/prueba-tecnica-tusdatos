from config.settings import Settings


def test_settings_load_sample_count():
    settings = Settings(
        target_url="https://www.g2.com",
        search_query="software metrics",
    )

    assert settings.sample_count >= 1


def test_settings_default_values():
    settings = Settings(
        target_url="https://www.g2.com",
        search_query="software metrics",
    )

    assert settings.max_attempts >= 1
    assert settings.base_delay >= 0
    assert settings.sample_delay >= 0


def test_settings_accepts_custom_sample_count():
    settings = Settings(
        target_url="https://www.g2.com",
        search_query="software metrics",
        sample_count=100,
    )

    assert settings.sample_count == 100