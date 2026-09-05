from pathlib import Path 
 
from metrics.scraper_metrics import ScraperMetrics 
 
 
class ReportGenerator: 
    '''
    Genera un reporte en formato Markdown a partir de las
    métricas recopiladas durante las ejecuciones del scraper.
    '''
 
    def __init__( 
        self, 
        output_path: str = "reports/execution_report.md", 
    ): 
        self.output_path = Path(output_path) 
 
    def generate( 
        self, 
        metrics: ScraperMetrics, 
    ) -> None: 
        '''
        Genera el contenido del reporte con las métricas
        de ejecución y lo guarda en el archivo configurado.
        '''
 
        summary = metrics.summary() 
 
        content = f"""# Scraper Execution Report 
 
## Metrics 
 
| Metric | Value | 
|---|---:| 
| Total requests | {summary["total_requests"]} | 
| Successful requests | {summary["successful_requests"]} | 
| Failed requests | {summary["failed_requests"]} | 
| Success rate | {summary["success_rate"]:.2f}% | 
| Failure rate | {summary["failure_rate"]:.2f}% | 
| Average execution time | {summary["average_execution_time"]:.2f} s | 
| Average attempts | {summary["average_attempts"]:.2f} | 
""" 
 
        self.output_path.parent.mkdir( 
            parents=True, 
            exist_ok=True, 
        ) 
 
        self.output_path.write_text( 
            content, 
            encoding="utf-8", 
        )