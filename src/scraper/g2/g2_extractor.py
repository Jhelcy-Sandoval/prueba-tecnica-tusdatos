from playwright.async_api import Page

class G2Extractor:
    """Extrae información de productos desde G2."""

    async def extract(self, page: Page) -> dict:
        product_name = await self._extract_product_name(page)

        return {
            "product_name": product_name,
            "product_url": page.url,
        }

    async def _extract_product_name(self, page: Page) -> str:
        
        locator = page.locator("h1").first

        if await locator.count() == 0:
            return ""

        product_name = (await locator.inner_text()).strip()

        suffixes = [
            " reviews and product details",
            " reviews",
        ]

        for suffix in suffixes:
            if product_name.endswith(suffix):
                product_name = product_name.removesuffix(suffix)

        return product_name.strip()