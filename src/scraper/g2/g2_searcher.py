import asyncio 
 
from playwright.async_api import Page 
 
 
class G2Searcher: 
    '''
    Gestiona las búsquedas dentro de G2.
    '''
 
    SEARCH_INPUT = 'input[name="query"]' 
    SEARCH_BUTTON = 'button.submit-search-btn[type="submit"]' 
 
    def __init__(self, search_query: str | None = None): 
        '''
        Inicializa el buscador con el término de búsqueda configurado.
        '''
        self.search_query = search_query 
 
    async def search(self, page: Page) -> bool: 
        '''
        Ejecuta una búsqueda en G2 utilizando el término configurado.
        '''
 
        if not self.search_query: 
            return False 
 
        search_input = page.locator( 
            self.SEARCH_INPUT 
        ).first 
 
        if await search_input.count() == 0: 
            print("Buscador de G2 no encontrado.") 
            return False 
 
        if not await search_input.is_visible(): 
            print("Buscador de G2 no visible.") 
            return False 
 
        await search_input.click() 
        await search_input.fill(self.search_query) 
 
        print(f"Consulta escrita: {self.search_query}") 
 
        await asyncio.sleep(2) 
 
        return await self._submit_search(page) 
 
    async def _submit_search(self, page: Page) -> bool: 
        '''
        Envía la consulta y espera la carga de los resultados
        de búsqueda.
        '''
 
        search_button = page.locator( 
            self.SEARCH_BUTTON 
        ).first 
 
        if await search_button.count() == 0: 
            print("Botón de búsqueda no encontrado.") 
            return False 
 
        print("Botón de búsqueda encontrado.") 
        print("Enviando búsqueda...") 
 
        await search_button.click() 
 
        try: 
            await page.wait_for_load_state( 
                "domcontentloaded", 
                timeout=10_000, 
            ) 
        except Exception as error: 
            print( 
                f"No se pudo esperar la carga después " 
                f"de la búsqueda: {error}" 
            ) 
 
        await asyncio.sleep(3) 
 
        print("URL:", page.url) 
        print("Título:", await page.title()) 
 
        return True