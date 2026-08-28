from pydantic import BaseModel, Field, HttpUrl

class Product(BaseModel):
    product_name: str = Field(min_length=1)
    product_url: HttpUrl