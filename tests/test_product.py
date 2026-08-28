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