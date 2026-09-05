from abc import ABC, abstractmethod

from playwright.async_api import Page


class CaptchaProvider(ABC):
    """Define el contrato para proveedores de CAPTCHA."""

    @abstractmethod
    async def is_blocked(
        self,
        page: Page,
    ) -> bool:
        """Determina si la página está bloqueada por CAPTCHA."""
        raise NotImplementedError

    @abstractmethod
    async def solve(
        self,
        page: Page,
    ) -> bool:
        """Intenta resolver el CAPTCHA detectado."""
        raise NotImplementedError