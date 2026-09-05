from dataclasses import dataclass

from config.settings import Settings


@dataclass
class RetryPolicy:
    '''
    Define la estrategia de reintentos utilizada por
    el scraper ante errores recuperables.
    '''

    max_attempts: int
    base_delay: float
    manual_intervention_delay: float

    @classmethod
    def from_settings(cls, settings: Settings) -> "RetryPolicy":
        '''
        Crea una política de reintentos utilizando los valores
        definidos en la configuración de la aplicación.
        '''

        return cls(
            max_attempts=settings.max_attempts,
            base_delay=settings.base_delay,
            manual_intervention_delay=(
                settings.manual_intervention_delay
            ),
        )

    def should_retry(self, attempt: int) -> bool:
        '''
        Determina si el scraper puede realizar otro intento
        según el número máximo de intentos configurado.
        '''

        return attempt < self.max_attempts

    def get_delay(self, attempt: int) -> float:
        '''
        Calcula el tiempo de espera antes del siguiente intento
        utilizando un incremento exponencial basado en el intento actual.
        '''

        return self.base_delay * (2 ** attempt)

    def get_manual_intervention_delay(self) -> float:
        '''
        Retorna el tiempo configurado para los casos que
        requieren intervención manual.
        '''

        return self.manual_intervention_delay