from metrics.scraper_metrics import ScraperMetrics
from validation.product import Product
from validation.scraping_result import ScrapingResult


def create_product() -> Product:
    return Product(
        product_name="Metric.ai",
        product_url="https://www.g2.com/products/metric-ai/reviews",
    )


def test_record_successful_request():
    metrics = ScraperMetrics()

    result = ScrapingResult(
        product=create_product(),
        access_status="success",
        attempts=1,
    )

    metrics.record(result, execution_time=2.5)

    assert metrics.total_requests == 1
    assert metrics.successful_requests == 1
    assert metrics.failed_requests == 0
    assert metrics.total_attempts == 1
    assert metrics.execution_times == [2.5]


def test_record_failed_request():
    metrics = ScraperMetrics()

    result = ScrapingResult(
        product=None,
        access_status="failed",
        attempts=3,
        failure_reason="CaptchaDetectedError",
    )

    metrics.record(result, execution_time=6.0)

    assert metrics.total_requests == 1
    assert metrics.successful_requests == 0
    assert metrics.failed_requests == 1
    assert metrics.total_attempts == 3
    assert metrics.execution_times == [6.0]


def test_calculate_rates():
    metrics = ScraperMetrics()

    success = ScrapingResult(
        product=create_product(),
        access_status="success",
        attempts=1,
    )

    failure = ScrapingResult(
        product=None,
        access_status="failed",
        attempts=3,
        failure_reason="CaptchaDetectedError",
    )

    metrics.record(success, execution_time=2.0)
    metrics.record(failure, execution_time=4.0)

    assert metrics.success_rate == 50.0
    assert metrics.failure_rate == 50.0


def test_calculate_average_execution_time():
    metrics = ScraperMetrics()

    result = ScrapingResult(
        product=create_product(),
        access_status="success",
        attempts=1,
    )

    metrics.record(result, execution_time=2.0)
    metrics.record(result, execution_time=4.0)

    assert metrics.average_execution_time == 3.0


def test_calculate_average_attempts():
    metrics = ScraperMetrics()

    result_one = ScrapingResult(
        product=create_product(),
        access_status="success",
        attempts=1,
    )

    result_two = ScrapingResult(
        product=create_product(),
        access_status="success",
        attempts=3,
    )

    metrics.record(result_one, execution_time=2.0)
    metrics.record(result_two, execution_time=4.0)

    assert metrics.average_attempts == 2.0


def test_summary():
    metrics = ScraperMetrics()

    result = ScrapingResult(
        product=create_product(),
        access_status="success",
        attempts=1,
    )

    metrics.record(result, execution_time=2.5)

    summary = metrics.summary()

    assert summary["total_requests"] == 1
    assert summary["successful_requests"] == 1
    assert summary["failed_requests"] == 0
    assert summary["success_rate"] == 100.0
    assert summary["failure_rate"] == 0.0
    assert summary["average_execution_time"] == 2.5
    assert summary["average_attempts"] == 1.0