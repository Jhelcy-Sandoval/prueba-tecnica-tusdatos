import pytest
from pydantic import ValidationError

from validation.product import Product


def test_product_is_valid():
    product = Product(
        product_name="Metric.ai",
        product_url="https://www.g2.com/products/metric-ai/reviews",
    )

    assert product.product_name == "Metric.ai"
    assert str(product.product_url) == (
        "https://www.g2.com/products/metric-ai/reviews"
    )


def test_product_name_cannot_be_empty():
    with pytest.raises(ValidationError):
        Product(
            product_name="",
            product_url="https://www.g2.com/products/metric-ai/reviews",
        )


def test_product_url_must_be_valid():
    with pytest.raises(ValidationError):
        Product(
            product_name="Metric.ai",
            product_url="not-a-valid-url",
        )