from dataclasses import dataclass

from config.settings import Settings


@dataclass
class RetryPolicy:
    """Define la estrategia de reintentos del scraper."""

    max_attempts: int
    base_delay: float
    manual_intervention_delay: float

    @classmethod
    def from_settings(cls, settings: Settings) -> "RetryPolicy":
        """Crea la política de reintentos desde la configuración."""

        return cls(
            max_attempts=settings.max_attempts,
            base_delay=settings.base_delay,
            manual_intervention_delay=(
                settings.manual_intervention_delay
            ),
        )

    def should_retry(self, attempt: int) -> bool:
        """Determina si se debe realizar otro intento."""

        return attempt < self.max_attempts

    def get_delay(self, attempt: int) -> float:
        """Calcula el tiempo de espera entre reintentos."""

        return self.base_delay * (2 ** attempt)

    def get_manual_intervention_delay(self) -> float:
        """Obtiene el tiempo para intervención manual."""

        return self.manual_intervention_delay