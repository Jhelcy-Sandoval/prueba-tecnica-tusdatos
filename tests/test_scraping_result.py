from validation.product import Product
from validation.scraping_result import ScrapingResult


def test_scraping_result_success():
    product = Product(
        product_name="Metric.ai",
        product_url="https://www.g2.com/products/metric-ai/reviews",
    )

    result = ScrapingResult(
        product=product,
        access_status="success",
        attempts=1,
    )

    assert result.product == product
    assert result.access_status == "success"
    assert result.attempts == 1
    assert result.failure_reason is None


def test_scraping_result_failure():
    result = ScrapingResult(
        access_status="failed",
        attempts=3,
        failure_reason="CaptchaDetectedError",
    )

    assert result.product is None
    assert result.access_status == "failed"
    assert result.attempts == 3
    assert result.failure_reason == "CaptchaDetectedError"