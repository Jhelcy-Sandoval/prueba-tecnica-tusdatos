import asyncio
from playwright.async_api import Page

class CaptchaProvider:

    async def solve(self, page: Page) -> bool:
        captcha_selector = 'iframe[title="DataDome CAPTCHA"]'

        # 1. Esperar a que el iframe esté presente
        try:
            await page.locator(captcha_selector).wait_for(
                state="attached",
                timeout=10_000,
            )
        except Exception:
            print("iframe no encontrado.")
            return False

        await asyncio.sleep(2)

        frame = page.frame_locator(captcha_selector)

        slider_container = frame.locator(".sliderContainer")

        try:
            await slider_container.wait_for(
                state="attached",
                timeout=10_000,
            )
        except Exception:
            print(".sliderContainer no encontrado.")
            return False

        slider = frame.locator(".slider")

        count = await slider.count()
        print(f".slider encontrado: {count}")
        
        if count == 0:
            return False

        try:
            await slider.fill("100")
            return True
        except Exception:
            pass

        try:
            box = await slider.bounding_box()
            if box:
                start_x = box["x"] + box["width"] / 2
                start_y = box["y"] + box["height"] / 2
                
                target_distance = 200  
                half_distance = target_distance / 2

                await page.mouse.move(start_x, start_y)
                await page.mouse.down()

                await page.mouse.move(start_x + half_distance, start_y, steps=30)

                await asyncio.sleep(0.8)

                await page.mouse.move(start_x + target_distance, start_y, steps=30)

                await page.mouse.up()
                return True

        except Exception as e:
            print(f"Error al interactuar con el slider: {e}")

        return False
    
    async def is_blocked(
        self,
        page: Page,
    ) -> bool:

        await asyncio.sleep(2)

        captcha_selector = (
            'iframe[title="DataDome CAPTCHA"]'
        )

        captcha = page.locator(
            captcha_selector
        )

        if await captcha.count() == 0:
            print(
                "iframe DataDome no encontrado."
            )
            return False

        frame = page.frame_locator(
            captcha_selector
        )

        blocked = frame.locator(
            '[data-dd-response-page="hard-block"]'
        )

        count = await blocked.count()

        print(
            f"Indicador hard-block encontrado: {count}"
        )

        return count > 0