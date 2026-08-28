import csv
from pathlib import Path

from validation.scraping_result import ScrapingResult


class DatasetWriter:
    """Guarda los resultados de scraping en un archivo CSV."""

    def __init__(self, file_path: str = "data/dataset.csv"):
        self.file_path = Path(file_path)

    def save(
        self,
        result: ScrapingResult,
        execution_time: float,
    ) -> None:
        """Agrega una ejecución al dataset."""

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
                    "access_status",
                    "attempts",
                    "execution_time",
                    "failure_reason",
                ],
            )

            if not file_exists:
                writer.writeheader()

            product_name = ""
            product_url = ""

            if result.product is not None:
                product_name = result.product.product_name
                product_url = str(result.product.product_url)

            writer.writerow(
                {
                    "product_name": product_name,
                    "product_url": product_url,
                    "access_status": result.access_status,
                    "attempts": result.attempts,
                    "execution_time": execution_time,
                    "failure_reason": result.failure_reason or "",
                }
            )