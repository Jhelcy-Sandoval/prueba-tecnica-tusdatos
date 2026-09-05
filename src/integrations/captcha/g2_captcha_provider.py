import asyncio 
import random 
import math 
from playwright.async_api import Page 
from integrations.captcha.captcha_provider import CaptchaProvider 
 
class G2CaptchaProvider(CaptchaProvider): 
    '''
    Implementa el manejo de los mecanismos de CAPTCHA
    utilizados por G2/DataDome.
    '''
 
    CAPTCHA_SELECTOR = 'iframe[title="DataDome CAPTCHA"]' 
    SLIDER_CONTAINER_SELECTOR = ".sliderContainer" 
    SLIDER_SELECTOR = ".slider" 
    HARD_BLOCK_SELECTOR = '[data-dd-response-page="hard-block"]' 
 
    async def solve(self, page: Page) -> bool: 
        '''
        Gestiona el CAPTCHA de G2 mediante la interacción
        con el componente de verificación disponible en la página.
        '''
 
        try: 
            iframe_element = page.locator(self.CAPTCHA_SELECTOR) 
            await iframe_element.wait_for(state="attached", timeout=10_000) 
             
            iframe_box = await iframe_element.bounding_box() 
            if not iframe_box: 
                print("No se pudo calcular el bounding box del iframe.") 
                return False 
                 
        except Exception as error: 
            print(f"iframe CAPTCHA no encontrado: {error}") 
            return False 
 
        await asyncio.sleep(1.5) 
 
        frame = page.frame_locator(self.CAPTCHA_SELECTOR) 
        slider_container = frame.locator(self.SLIDER_CONTAINER_SELECTOR) 
        slider = frame.locator(self.SLIDER_SELECTOR) 
 
        try: 
            await slider_container.wait_for(state="visible", timeout=10_000) 
            if await slider.count() == 0: 
                print(".slider no encontrado dentro del iframe.") 
                return False 
        except Exception as error: 
            print(f"Componentes del slider no visibles: {error}") 
            return False 
 
        try: 
            container_box = await slider_container.bounding_box() 
            button_box = await slider.bounding_box() 
             
            if not container_box or not button_box: 
                print("Error calculando dimensiones de los elementos del slider.") 
                return False 
 
            total_distance = container_box["width"] - button_box["width"] + 5 
             
            start_x = iframe_box["x"] + button_box["x"] + (button_box["width"] / 2) 
            start_y = iframe_box["y"] + button_box["y"] + (button_box["height"] / 2) 
 
            print(f"Arrastrando slider. Distancia estimada: {total_distance}px desde X: {start_x}") 
 
            await page.mouse.move(start_x, start_y, steps=5) 
            await asyncio.sleep(0.2) 
            await page.mouse.down() 
            await asyncio.sleep(0.3) 
 
            current_x = start_x 
            steps = 45  
             
            for i in range(1, steps + 1): 
                fraction = i / steps 
                t = math.sin(fraction * (math.pi / 2)) 
                 
                target_x = start_x + (total_distance * t) 
                jitter_y = start_y + random.uniform(-1.5, 1.5) 
                 
                await page.mouse.move(target_x, jitter_y) 
                await asyncio.sleep(random.uniform(0.008, 0.02)) 
 
            await asyncio.sleep(random.uniform(0.4, 0.7)) 
            await page.mouse.up() 
             
            return True 
 
        except Exception as error: 
            print(f"Error al interactuar con el slider: {error}") 
 
        return False 
 
    async def is_blocked(self, page: Page) -> bool: 
        '''
        Detecta si DataDome presenta un bloqueo permanente
        y gestiona la recarga de la página para comprobar
        si el bloqueo persiste.
        '''
 
        await asyncio.sleep(2) 
        captcha = page.locator(self.CAPTCHA_SELECTOR) 
 
        if await captcha.count() == 0: 
            print("iframe DataDome no encontrado.") 
            return False 
 
        frame = page.frame_locator(self.CAPTCHA_SELECTOR) 
        blocked = frame.locator(self.HARD_BLOCK_SELECTOR) 
        count = await blocked.count() 
 
        print(f"Indicador hard-block encontrado: {count}") 
 
        if count == 0: 
            return False 
 
        print("DataDome detectó hard-block. Esperando antes de recargar...") 
        await asyncio.sleep(10) 
 
        print("Recargando la página...") 
        await page.reload(wait_until="domcontentloaded") 
        await asyncio.sleep(3) 
 
        captcha = page.locator(self.CAPTCHA_SELECTOR) 
        if await captcha.count() == 0: 
            print("CAPTCHA ya no está presente.") 
            return False 
 
        frame = page.frame_locator(self.CAPTCHA_SELECTOR) 
        blocked = frame.locator(self.HARD_BLOCK_SELECTOR) 
        count = await blocked.count() 
 
        print(f"Hard-block después de recargar: {count}") 
        return count > 0 