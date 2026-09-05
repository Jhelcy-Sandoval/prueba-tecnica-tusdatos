class ScraperError(Exception):
    '''
    Excepción base para los errores relacionados con
    el sistema de scraping.
    '''

    def __init__(self, message: str):
        '''
        Inicializa la excepción con el mensaje descriptivo
        del error.
        '''

        self.message = message
        super().__init__(message)


class CaptchaDetectedError(ScraperError):
    '''
    Representa la detección de un CAPTCHA durante
    el proceso de navegación.
    '''

    def __init__(self, message: str = "Se detectó un CAPTCHA."):
        '''
        Inicializa la excepción con el mensaje correspondiente
        a la detección de un CAPTCHA.
        '''

        super().__init__(message)


class AccessBlockedError(ScraperError):
    '''
    Representa un bloqueo de acceso a la fuente
    durante el proceso de scraping.
    '''

    def __init__(self, message: str = "El acceso a la fuente fue bloqueado."):
        '''
        Inicializa la excepción con el mensaje correspondiente
        al bloqueo de acceso.
        '''

        super().__init__(message)


class NavigationError(ScraperError):
    '''
    Representa un error ocurrido durante la navegación
    hacia el recurso solicitado.
    '''

    def __init__(self, message: str = "Ocurrió un error durante la navegación."):
        '''
        Inicializa la excepción con el mensaje correspondiente
        al error de navegación.
        '''

        super().__init__(message)