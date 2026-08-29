from urllib.parse import urlparse

from playwright.async_api import Page


class GoogleSearcher:

    async def search(
        self,
        page: Page,
        query: str,
        target_url: str,
    ) -> str | None:

        target_domain = urlparse(
            target_url
        ).netloc

        await page.goto(
            "https://www.google.com",
            wait_until="domcontentloaded",
        )

        search_box = page.locator(
            'textarea[name="q"], input[name="q"]'
        ).first

        await search_box.fill(query)

        await search_box.press("Enter")

        await page.wait_for_load_state(
            "domcontentloaded"
        )

        results = page.locator(
            'a[href]'
        )

        for index in range(
            await results.count()
        ):

            result = results.nth(index)

            href = await result.get_attribute(
                "href"
            )

            if not href:
                continue

            if target_domain in href:

                print(
                    f"Resultado encontrado: {href}"
                )

                return href

        return None