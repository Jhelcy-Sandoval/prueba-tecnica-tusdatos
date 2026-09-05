from pydantic import BaseModel, Field

from validation.product import Product


class ScrapingResult(BaseModel):
    '''
    Representa el resultado de una ejecución del scraper,
    incluyendo los productos obtenidos y el estado de la ejecución.
    '''

    products: list[Product] = Field(
        default_factory=list
    )

    access_status: str
    attempts: int = Field(ge=1)
    failure_reason: str | None = None