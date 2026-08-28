from pydantic import BaseModel, Field

from validation.product import Product

class ScrapingResult(BaseModel):
    """Representa el resultado de una ejecución del scraper."""

    product: Product | None = None
    access_status: str
    attempts: int = Field(ge=1)
    failure_reason: str | None = None