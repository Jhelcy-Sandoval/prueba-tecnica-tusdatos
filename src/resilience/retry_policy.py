from dataclasses import dataclass


@dataclass
class RetryPolicy:
    """Define la estrategia de reintentos del scraper."""

    max_attempts: int = 3
    base_delay: float = 2.0
    manual_intervention_delay: float = 30.0

    def should_retry(self, attempt: int) -> bool:
        return attempt < self.max_attempts

    def get_delay(self, attempt: int) -> float:
        return self.base_delay * (2 ** attempt)

    def get_manual_intervention_delay(self) -> float:
        return self.manual_intervention_delay