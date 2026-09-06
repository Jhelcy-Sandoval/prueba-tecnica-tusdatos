# Arquitectura del Sistema de Scraping (G2)

Este documento describe la arquitectura del sistema desarrollado para la extracción de información de productos desde G2, incluyendo la orquestación de ejecuciones, gestión de acceso, recuperación ante errores, rotación de entornos de ejecución, validación de datos, persistencia y generación de métricas y reportes.

## 1. Vista General de la Arquitectura

El sistema utiliza una arquitectura modular orientada a responsabilidades. El flujo inicia en `main.py`, donde se configuran e inicializan los componentes principales. `ScrapingRunner` coordina las ejecuciones y delega el proceso de extracción a `G2Scraper`.

`BrowserManager` gestiona el ciclo de vida del navegador y mantiene la referencia de la página activa. La ejecución inicial utiliza una conexión directa y, ante un bloqueo de acceso que requiera recuperación, permite crear un nuevo contexto utilizando el siguiente proxy configurado.

Durante el proceso de scraping, el sistema incorpora una capa específica para detectar y gestionar problemas de acceso, incluyendo verificaciones CAPTCHA y bloqueos permanentes de DataDome. Los resultados obtenidos son normalizados mediante modelos de validación y posteriormente utilizados para generar el dataset y las métricas de ejecución.

```mermaid
graph TD

    Main[main.py] --> BrowserManager[BrowserManager]

    Main --> ScrapingRunner[ScrapingRunner]

    BrowserManager --> BrowserContext[Browser Context]
    BrowserManager --> ActivePage[Active Page]
    BrowserManager --> ProxyConfig[Proxy Configuration]

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

        AccessDetector --> AccessResult[AccessResult]

    end

    subgraph Resilience [Resiliencia y Recuperación]

        G2Scraper --> RetryPolicy[RetryPolicy]
        G2Scraper --> BrowserManager
        BrowserManager --> ProxyRotation[Rotación de entorno]

    end

    G2Extractor --> Product[Product]

    G2Scraper --> ScrapingResult[ScrapingResult]

    subgraph Output_Processing [Procesamiento de Resultados]

        ScrapingResult --> DatasetWriter[DatasetWriter]
        ScrapingResult --> ScraperMetrics[ScraperMetrics]
        ScraperMetrics --> ReportGenerator[ReportGenerator]

    end