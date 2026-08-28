class ScraperError(Exception):
    """Excepción base para los errores del sistema de scraping."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class CaptchaDetectedError(ScraperError):
    """Indica que se detectó un CAPTCHA durante la navegación."""

    def __init__(self, message: str = "Se detectó un CAPTCHA."):
        super().__init__(message)


class AccessBlockedError(ScraperError):
    """Indica que el acceso a la fuente fue bloqueado."""

    def __init__(self, message: str = "El acceso a la fuente fue bloqueado."):
        super().__init__(message)


class NavigationError(ScraperError):
    """Indica que ocurrió un error durante la navegación."""

    def __init__(self, message: str = "Ocurrió un error durante la navegación."):
        super().__init__(message)