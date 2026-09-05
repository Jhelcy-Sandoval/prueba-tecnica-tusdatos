from dataclasses import dataclass, field

from validation.scraping_result import ScrapingResult


@dataclass
class ScraperMetrics:
    '''
    Acumula y calcula las métricas obtenidas durante
    las ejecuciones del scraper.
    '''

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_attempts: int = 0
    execution_times: list[float] = field(default_factory=list)

    def record(
        self,
        result: ScrapingResult,
        execution_time: float,
    ) -> None:
        '''
        Registra las métricas correspondientes a una
        ejecución del scraper.
        '''

        self.total_requests += 1
        self.total_attempts += result.attempts
        self.execution_times.append(execution_time)

        if result.products:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

    @property
    def success_rate(self) -> float:
        '''
        Calcula el porcentaje de ejecuciones que
        finalizaron con productos extraídos.
        '''

        if self.total_requests == 0:
            return 0.0

        return (
            self.successful_requests
            / self.total_requests
        ) * 100

    @property
    def failure_rate(self) -> float:
        '''
        Calcula el porcentaje de ejecuciones que
        finalizaron sin productos extraídos.
        '''

        if self.total_requests == 0:
            return 0.0

        return (
            self.failed_requests
            / self.total_requests
        ) * 100

    @property
    def average_execution_time(self) -> float:
        '''
        Calcula el tiempo promedio de ejecución
        de las muestras procesadas.
        '''

        if not self.execution_times:
            return 0.0

        return (
            sum(self.execution_times)
            / len(self.execution_times)
        )

    @property
    def average_attempts(self) -> float:
        '''
        Calcula el promedio de intentos realizados
        por cada ejecución.
        '''

        if self.total_requests == 0:
            return 0.0

        return (
            self.total_attempts
            / self.total_requests
        )

    def summary(self) -> dict:
        '''
        Devuelve un resumen con las métricas acumuladas
        durante las ejecuciones del scraper.
        '''

        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "average_execution_time": self.average_execution_time,
            "average_attempts": self.average_attempts,
        }