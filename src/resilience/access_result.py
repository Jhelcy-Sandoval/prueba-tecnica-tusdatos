from abc import ABC, abstractmethod

from resilience.exceptions import (
    AccessBlockedError,
    CaptchaDetectedError,
    NavigationError,
)


class AccessResult(ABC):
    '''
    Define el contrato para representar el resultado
    de una comprobación de acceso.
    '''

    @property
    @abstractmethod
    def status(self) -> str:
        '''
        Retorna el estado de acceso identificado.
        '''
        pass

    @abstractmethod
    def validate(self) -> None:
        '''
        Valida el resultado y genera una excepción cuando
        el estado requiere una acción de recuperación.
        '''
        pass


class AccessGranted(AccessResult):
    '''
    Representa un acceso concedido correctamente.
    '''

    @property
    def status(self) -> str:
        '''
        Retorna el estado correspondiente a un acceso exitoso.
        '''
        return "success"

    def validate(self) -> None:
        '''
        Valida un acceso concedido sin generar excepciones.
        '''
        pass


class CaptchaRequired(AccessResult):
    '''
    Representa un acceso que requiere gestionar un CAPTCHA.
    '''

    @property
    def status(self) -> str:
        '''
        Retorna el estado correspondiente a una verificación CAPTCHA.
        '''
        return "captcha"

    def validate(self) -> None:
        '''
        Indica que se requiere gestionar un CAPTCHA mediante
        la excepción correspondiente.
        '''
        raise CaptchaDetectedError(
            "Se detectó un CAPTCHA."
        )


class AccessBlocked(AccessResult):
    '''
    Representa un acceso bloqueado al recurso solicitado.
    '''

    @property
    def status(self) -> str:
        '''
        Retorna el estado correspondiente a un acceso bloqueado.
        '''
        return "blocked"

    def validate(self) -> None:
        '''
        Indica que el acceso fue bloqueado mediante
        la excepción correspondiente.
        '''
        raise AccessBlockedError(
            "El acceso fue bloqueado."
        )


class AccessUnknown(AccessResult):
    '''
    Representa un estado de acceso que no pudo determinarse.
    '''

    @property
    def status(self) -> str:
        '''
        Retorna el estado correspondiente a un acceso desconocido.
        '''
        return "unknown"

    def validate(self) -> None:
        '''
        Indica que el estado de acceso no pudo determinarse
        mediante la excepción correspondiente.
        '''
        raise NavigationError(
            "No se pudo determinar el estado de acceso."
        )