import asyncio 
 
from playwright.async_api import Page 
 
from integrations.captcha.captcha_provider import CaptchaProvider 
 
 
class GoogleCaptchaProvider(CaptchaProvider): 
    '''
    Implementa el manejo de las verificaciones solicitadas
    por Google durante el proceso de búsqueda.
    '''
 
    async def is_blocked( 
        self, 
        page: Page, 
    ) -> bool: 
        '''
        Detecta si Google solicita una verificación
        mediante la URL actual de la página.
        '''
 
        return "/sorry/" in page.url 
 
    async def solve( 
            self, 
            page: Page, 
        ) -> bool: 
            '''
            Espera la intervención manual del usuario para
            gestionar la verificación solicitada por Google.
            '''
 
            print("Google solicitó una verificación.") 
            print( 
                "Se requiere intervención manual " 
                "para continuar." 
            ) 
            print("Tienes 30 segundos para resolverla...") 
 
            await asyncio.sleep(30) 
 
            return True