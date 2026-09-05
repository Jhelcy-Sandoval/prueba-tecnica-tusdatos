import csv
from pathlib import Path

from validation.scraping_result import ScrapingResult


class DatasetWriter:
    '''
    Guarda los resultados de las ejecuciones del scraper
    en un archivo CSV.
    '''

    FIELDNAMES = [
        "sample_id",
        "product_name",
        "product_url",
        "rating",
        "reviews",
        "access_status",
        "attempts",
        "execution_time",
        "failure_reason",
    ]

    def __init__(
        self,
        file_path: str = "data/dataset.csv",
    ):
        '''
        Inicializa el escritor con la ruta del archivo
        donde se almacenará el dataset.
        '''

        self.file_path = Path(file_path)

    def save(
        self,
        result: ScrapingResult,
        execution_time: float,
        sample_id: int,
    ) -> None:
        '''
        Agrega al dataset los productos obtenidos en una
        ejecución junto con sus datos de ejecución y estado.
        '''

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
                fieldnames=self.FIELDNAMES,
            )

            if not file_exists:
                writer.writeheader()

            for product in result.products:
                writer.writerow(
                    {
                        "sample_id": sample_id,
                        "product_name": product.product_name,
                        "product_url": str(
                            product.product_url
                        ),
                        "rating": product.rating,
                        "reviews": product.reviews,
                        "access_status": result.access_status,
                        "attempts": result.attempts,
                        "execution_time": execution_time,
                        "failure_reason": (
                            result.failure_reason or ""
                        ),
                    }
                )