import csv

from persistence.dataset_writer import DatasetWriter
from validation.product import Product
from validation.scraping_result import ScrapingResult


def create_product(
    name: str = "Metric.ai",
    url: str = "https://www.g2.com/products/metric-ai/reviews",
) -> Product:
    return Product(
        product_name=name,
        product_url=url,
    )


def create_success_result(
    product: Product,
) -> ScrapingResult:
    return ScrapingResult(
        products=[product],
        access_status="success",
        attempts=1,
    )


def test_dataset_writer_creates_csv(tmp_path):
    file_path = tmp_path / "dataset.csv"

    product = create_product()
    result = create_success_result(product)

    writer = DatasetWriter(str(file_path))

    writer.save(
        result,
        execution_time=2.5,
        sample_id=1,
    )

    assert file_path.exists()

    with file_path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["sample_id"] == "1"
    assert rows[0]["product_name"] == "Metric.ai"
    assert rows[0]["product_url"] == (
        "https://www.g2.com/products/metric-ai/reviews"
    )
    assert rows[0]["access_status"] == "success"
    assert rows[0]["attempts"] == "1"
    assert rows[0]["execution_time"] == "2.5"
    assert rows[0]["failure_reason"] == ""


def test_dataset_writer_appends_products(tmp_path):
    file_path = tmp_path / "dataset.csv"

    writer = DatasetWriter(str(file_path))

    product_1 = create_product()

    product_2 = create_product(
        name="Product 2",
        url="https://www.g2.com/products/product-2/reviews",
    )

    result_1 = create_success_result(product_1)
    result_2 = create_success_result(product_2)

    writer.save(
        result_1,
        execution_time=2.0,
        sample_id=1,
    )

    writer.save(
        result_2,
        execution_time=3.0,
        sample_id=2,
    )

    with file_path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 2

    assert rows[0]["sample_id"] == "1"
    assert rows[0]["product_name"] == "Metric.ai"

    assert rows[1]["sample_id"] == "2"
    assert rows[1]["product_name"] == "Product 2"


def test_dataset_writer_saves_multiple_products(tmp_path):
    file_path = tmp_path / "dataset.csv"

    products = [
        create_product(),
        create_product(
            name="Product 2",
            url="https://www.g2.com/products/product-2/reviews",
        ),
    ]

    result = ScrapingResult(
        products=products,
        access_status="success",
        attempts=1,
    )

    writer = DatasetWriter(str(file_path))

    writer.save(
        result,
        execution_time=2.5,
        sample_id=1,
    )

    with file_path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 2
    assert rows[0]["sample_id"] == "1"
    assert rows[1]["sample_id"] == "1"
    assert rows[0]["product_name"] == "Metric.ai"
    assert rows[1]["product_name"] == "Product 2"