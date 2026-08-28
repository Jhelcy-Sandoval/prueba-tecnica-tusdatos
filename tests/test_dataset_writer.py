from persistence.dataset_writer import DatasetWriter
from validation.product import Product


def test_dataset_writer_creates_csv(tmp_path):
    file_path = tmp_path / "dataset.csv"

    product = Product(
        product_name="Metric.ai",
        product_url="https://www.g2.com/products/metric-ai/reviews",
    )

    writer = DatasetWriter(str(file_path))

    writer.save(product)

    assert file_path.exists()

    content = file_path.read_text(encoding="utf-8")

    assert "product_name,product_url" in content
    assert "Metric.ai" in content
    assert "https://www.g2.com/products/metric-ai/reviews" in content
    
def test_dataset_writer_appends_products(tmp_path):
    file_path = tmp_path / "dataset.csv"

    writer = DatasetWriter(str(file_path))

    product_1 = Product(
        product_name="Metric.ai",
        product_url="https://www.g2.com/products/metric-ai/reviews",
    )

    product_2 = Product(
        product_name="Product 2",
        product_url="https://www.g2.com/products/product-2/reviews",
    )

    writer.save(product_1)
    writer.save(product_2)

    content = file_path.read_text(encoding="utf-8")

    assert "Metric.ai" in content
    assert "Product 2" in content

    assert content.count("product_name,product_url") == 1