# Arquitectura del Sistema de Scraping (G2)

Este documento describe la arquitectura del sistema desarrollado para la extracción de información de productos desde G2, incluyendo la orquestación de ejecuciones, gestión de acceso, recuperación ante errores, validación de datos, persistencia y generación de métricas y reportes.

## 1. Vista General de la Arquitectura

El sistema utiliza una arquitectura modular orientada a responsabilidades. El flujo inicia en `main.py`, donde se configuran e inicializan los componentes principales. `ScrapingRunner` coordina las ejecuciones y delega el proceso de extracción a `G2Scraper`.

Durante el proceso de scraping, el sistema incorpora una capa específica para detectar y gestionar problemas de acceso, incluyendo verificaciones CAPTCHA. Los resultados obtenidos son normalizados mediante modelos de validación y posteriormente utilizados para generar el dataset y las métricas de ejecución.

```mermaid
graph TD

    Main[main.py] --> BrowserManager[BrowserManager]
    Main --> ScrapingRunner[ScrapingRunner]

    ScrapingRunner --> GoogleSearcher[GoogleSearcher]
    ScrapingRunner --> G2Scraper[G2Scraper]

    subgraph Core_Scraping [Núcleo de Scraping]
        G2Scraper --> G2Searcher[G2Searcher]
        G2Scraper --> G2Extractor[G2Extractor]
        G2Scraper --> AccessHandler[AccessHandler]
        G2Extractor --> G2UIHandler[G2UIHandler]
    end

    subgraph Access_Management [Gestión de Acceso]
        AccessHandler --> AccessDetector[AccessDetector]
        AccessHandler --> CaptchaProvider[CaptchaProvider]
        CaptchaProvider --> G2CaptchaProvider[G2CaptchaProvider]
    end

    G2Extractor --> Product[Product]
    G2Scraper --> ScrapingResult[ScrapingResult]

    subgraph Output_Processing [Procesamiento de Resultados]
        ScrapingResult --> DatasetWriter[DatasetWriter]
        ScrapingResult --> ScraperMetrics[ScraperMetrics]
        ScraperMetrics --> ReportGenerator[ReportGenerator]
    end