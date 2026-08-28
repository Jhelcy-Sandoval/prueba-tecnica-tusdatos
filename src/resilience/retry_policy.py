from dataclasses import dataclass

@dataclass
class RetryPolicy:
    # politica de reintentos
    max_attempts: int = 3
    base_delay: float = 2.0

    def should_retry(self, attempt: int) -> bool:
        return attempt < self.max_attempts

    def get_delay(self, attempt: int) -> float:
        return self.base_delay * (2 ** attempt)