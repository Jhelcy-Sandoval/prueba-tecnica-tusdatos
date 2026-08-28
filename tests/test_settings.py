from config.settings import Settings


def test_settings_load_sample_count():
    settings = Settings()

    assert settings.sample_count >= 1