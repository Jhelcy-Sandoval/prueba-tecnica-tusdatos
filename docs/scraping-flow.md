# Flujo de Scraping (G2)

Este documento describe el flujo de ejecución del sistema de scraping para G2: la secuencia de pasos que ocurre desde la inicialización hasta la persistencia de resultados, incluyendo los puntos de verificación de acceso, la renovación periódica de contextos y las decisiones que puede tomar el sistema en cada etapa.

Este documento complementa la [Arquitectura del Sistema](./architecture.md) y la [Estrategia de Resiliencia](./resilience.md): mientras esos documentos describen *componentes* y *manejo de errores*, este describe el *orden temporal* en que ocurren las cosas.

---

## 1. Visión General del Flujo

El flujo se ejecuta una vez por cada muestra (`sample_id`), agrupadas en **bloques de 5 muestras**, y se repite hasta completar el total configurado (`SAMPLE_COUNT`). Una muestra fallida no detiene el proceso: `ScrapingRunner` continúa con la siguiente. Al completar cada bloque de 5, el contexto de navegación se destruye y se crea uno nuevo, reiniciando la localización de G2 desde Google (ver [`resilience.md`](./resilience.md), sección 5).

```mermaid
flowchart TD
    A[main.py: cargar Settings] --> B[BrowserManager: crear contexto]
    B --> C[GoogleSearcher: localizar URL de G2]
    C --> D[ScrapingRunner: iniciar muestra del bloque]
    D --> E[G2Scraper: navegar a G2]
    E --> F{AccessDetector: verificar acceso}
    F -->|AccessGranted| G[G2Searcher: buscar dentro de G2]
    F -->|CaptchaRequired| H[AccessHandler → CaptchaProvider]
    F -->|AccessBlocked| I[AccessBlockedError → RetryPolicy]
    H --> F
    I -->|retry disponible| E
    I -->|intentos agotados| J[Marcar muestra como failed]
    G --> K[G2Extractor: identificar candidatos]
    K --> L[G2ProductExtractor: abrir producto]
    L --> M{AccessDetector: verificar acceso}
    M -->|AccessGranted| N[G2ProductValidator: confirmar producto esperado]
    M -->|CaptchaRequired/AccessBlocked| H
    N --> O[G2ProductDataExtractor + G2SelectorResolver: extraer rating/reviews]
    O --> P[Product: validar con Pydantic]
    P --> Q[Construir ScrapingResult]
    J --> Q
    Q --> R[DatasetWriter: persistir fila]
    Q --> S[ScraperMetrics: registrar métricas]
    R --> T{¿Muestra 5 del bloque?}
    S --> T
    T -->|no| D
    T -->|sí, quedan muestras| U[BrowserManager: destruir y recrear contexto]
    U --> C
    T -->|sí, no quedan muestras| V[ReportGenerator: generar reporte final]
```

---

## 2. Etapas del Flujo

| # | Etapa | Componente responsable | Descripción |
|---|---|---|---|
| 1 | Configuración | `Settings` | Carga variables de entorno (`SAMPLE_COUNT`, `HEADLESS`, `MAX_PRODUCTS`, etc.). |
| 2 | Creación de contexto | `BrowserManager` | Crea un contexto de Playwright, reutilizado dentro del bloque actual de 5 muestras. |
| 3 | Localización de G2 | `GoogleSearcher` | Encuentra la URL de G2 a partir de una búsqueda en Google. Se repite al inicio de cada bloque nuevo. |
| 4 | Inicio de muestra | `ScrapingRunner` | Asigna `sample_id`, arranca el cronómetro de `execution_time`. |
| 5 | Navegación | `G2Scraper` | Navega a la página objetivo dentro de G2. |
| 6 | Verificación de acceso | `AccessDetector` | Determina el estado: `AccessGranted`, `CaptchaRequired`, `AccessBlocked` o `AccessUnknown`. |
| 7 | Gestión de CAPTCHA | `AccessHandler` + `CaptchaProvider` | Si el estado es `CaptchaRequired`, delega la resolución y vuelve a verificar. |
| 8 | Recuperación de bloqueo | `RetryPolicy` | Si el estado es `AccessBlocked`, aplica backoff exponencial y reintenta. |
| 9 | Búsqueda interna | `G2Searcher` | Busca el término dentro de G2 una vez hay acceso. |
| 10 | Identificación de candidatos | `G2Extractor` | Normaliza URLs relativas, elimina duplicados, limita a `MAX_PRODUCTS`. |
| 11 | Apertura de producto | `G2ProductExtractor` + `G2UIHandler` | Abre una página nueva por producto dentro del mismo contexto; `G2UIHandler` gestiona elementos de UI que interfieren. |
| 12 | Re-verificación de acceso | `AccessDetector` | Se repite la verificación por cada producto abierto. |
| 13 | Validación de producto | `G2ProductValidator` | Confirma que la página cargada corresponde al producto candidato esperado. |
| 14 | Extracción de datos | `G2ProductDataExtractor` + `G2SelectorResolver` | Extrae `rating` y `reviews`, probando selectores alternativos si el principal no está disponible. |
| 15 | Validación de esquema | `Product` (Pydantic) | Normaliza reviews (`'(7,964)'` → `7964`), convierte rating a `float`, valida `product_url` como `HttpUrl`. |
| 16 | Construcción del resultado | `ScrapingResult` | Agrupa productos, `access_status`, `attempts`, `failure_reason`. |
| 17 | Persistencia | `DatasetWriter` | Escribe una fila por producto en el dataset CSV. |
| 18 | Medición | `ScraperMetrics` | Acumula `success_rate`, `failure_rate`, `average_execution_time`, `average_attempts`. |
| 19 | Renovación de contexto | `BrowserManager` | Cada 5 muestras, destruye el contexto actual y crea uno nuevo (vuelve al paso 2-3). |
| 20 | Repetición | `ScrapingRunner` | Continúa con la siguiente muestra/bloque hasta agotar `SAMPLE_COUNT`. |
| 21 | Reporte final | `ReportGenerator` | Genera el reporte consolidado tras procesar todas las muestras. |

---

## 3. Puntos de Decisión Clave

- **¿El acceso fue exitoso?** → continúa el flujo normal (búsqueda/extracción).
- **¿Se detectó CAPTCHA?** → se delega a `CaptchaProvider`; tras la gestión, se vuelve a verificar el acceso antes de continuar.
- **¿Se detectó bloqueo (`AccessBlocked`)?** → se lanza una excepción (`AccessBlockedError`) y `RetryPolicy` decide si reintentar con backoff (`delay = base_delay * 2^attempt`) o marcar la muestra como `failed`.
- **¿Se agotaron los intentos?** → la muestra se registra como `failed` con su `failure_reason`, y `ScrapingRunner` continúa con la siguiente sin detener el proceso completo.
- **¿No se encuentra el selector principal de rating/reviews?** → `G2SelectorResolver` prueba selectores alternativos antes de considerar el dato como no disponible.
- **¿Se completó el bloque de 5 muestras?** → `BrowserManager` destruye el contexto actual, crea uno nuevo, y el flujo reinicia desde `GoogleSearcher` para el siguiente bloque.

---

## 4. Salida del Flujo

Al finalizar las `SAMPLE_COUNT` muestras, el sistema produce tres artefactos:

1. **Dataset CSV** (`DatasetWriter`): una fila por producto, con columnas de negocio (`product_name`, `product_url`, `rating`, `reviews`) y columnas operacionales (`sample_id`, `access_status`, `attempts`, `execution_time`, `failure_reason`).
2. **Métricas** (`ScraperMetrics`): `total_requests`, `successful_requests`, `failed_requests`, `success_rate`, `failure_rate`, `average_execution_time`, `average_attempts`.
3. **Reporte final** (`ReportGenerator`): consolida las métricas anteriores en un formato legible para análisis. Requiere que el proceso complete todas las muestras configuradas; una interrupción no controlada antes del final (ver [`resilience.md`](./resilience.md), sección 12) impide que este reporte se genere automáticamente.