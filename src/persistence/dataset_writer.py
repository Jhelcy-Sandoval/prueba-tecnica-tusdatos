import csv
from pathlib import Path

from validation.product import Product


class DatasetWriter:
    """Guarda productos validados en un archivo CSV."""

    def __init__(self, file_path: str = "data/dataset.csv"):
        self.file_path = Path(file_path)

    def save(self, product: Product) -> None:
        """Agrega un producto al dataset."""

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_exists = self.file_path.exists()

        with self.file_path.open(
            mode="a",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "product_name",
                    "product_url",
                ],
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow(
                product.model_dump(mode="json")
            )