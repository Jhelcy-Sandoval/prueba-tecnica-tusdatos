from pydantic import BaseModel, Field, HttpUrl


class Product(BaseModel):
    '''
    Representa la información normalizada de un producto
    obtenido durante el proceso de scraping.
    '''

    product_name: str = Field(min_length=1)

    product_url: HttpUrl

    rating: float | None = None

    reviews: int | None = None