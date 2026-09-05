# Sistema de Scraping Resiliente para G2

Motor de extracción de información de productos desde G2 diseñado para procesar múltiples ejecuciones con alta tasa de éxito e integridad de datos, manteniendo continuidad ante fallos de acceso (bloqueos y CAPTCHA), validando los datos extraídos y generando dataset y métricas para evaluar éxito, estabilidad y latencia.

**Idea central:** detectar → gestionar → reintentar → validar → registrar → medir → continuar.

---

## Documentación técnica

| Documento | Contenido |
|---|---|
| [`arquitectura.md`](./docs/architecture.md) | Componentes del sistema, responsabilidades y diagrama de dependencias. |
| [`scraping-flow.md`](./docs/scraping-flow.md) | Secuencia de ejecución paso a paso, desde la configuración hasta el reporte final. |
| [`resiliencia.md`](./docs/resilience.md) | Detección de acceso, gestión de CAPTCHA, `RetryPolicy` y backoff exponencial. |

---

## Requisitos del desafío

| Requisito | Implementación |
|---|---|
| 100 ejecuciones | `ScrapingRunner` + `sample_count` + `sample_id`. |
| Continuidad | Una muestra fallida no detiene las siguientes. |
| Bloqueos / CAPTCHA | `AccessDetector` + `AccessHandler` + `CaptchaProvider`. |
| Recuperación | `RetryPolicy` + backoff exponencial. |
| Integridad | `Product` + `ScrapingResult` (validación con Pydantic). |
| Trazabilidad | `sample_id`, `attempts`, `execution_time`, `access_status`, `failure_reason`. |
| Métricas | `ScraperMetrics`. |
| Dataset | `DatasetWriter`. |
| Reporte | `ReportGenerator`. |
| Reproducibilidad | `Dockerfile` + `docker-compose.yml` + `.dockerignore`. |

Las 100 solicitudes se modelan como 100 ejecuciones independientes. Una ejecución puede generar varios registros de producto (hasta `MAX_PRODUCTS` filas por muestra); `sample_id` conserva la relación entre cada registro y su ejecución.

---

## Instalación

```bash
git clone <url-del-repositorio>
cd <nombre-del-repositorio>
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

---

## Configuración

Variables de entorno principales (definidas en `Settings`):

| Variable | Descripción | Valor de ejemplo |
|---|---|---|
| `SAMPLE_COUNT` | Número de ejecuciones a procesar. | `100` |
| `HEADLESS` | Si el navegador corre sin interfaz gráfica. | `false` (recomendado para la ejecución funcional local) |
| `MAX_PRODUCTS` | Máximo de productos extraídos por muestra. | `3` |

Crea un archivo `.env` en la raíz del proyecto con estas variables antes de ejecutar. **No subas `.env` al repositorio.**

---

## Ejecución

```bash
python main.py
```

El proceso:
1. Carga la configuración y levanta el navegador (Playwright).
2. Localiza G2 mediante `GoogleSearcher`.
3. Ejecuta `SAMPLE_COUNT` muestras, cada una con su propio `sample_id`.
4. Ante CAPTCHA o bloqueo, gestiona el acceso y reintenta según `RetryPolicy`.
5. Al finalizar, genera el dataset, las métricas y el reporte final.

Ver el detalle completo del flujo en [`scraping-flow.md`](./docs/scraping-flow.md).

---

## Salidas

### Dataset (`DatasetWriter`)

Archivo CSV con una fila por producto extraído:

```
sample_id,product_name,product_url,rating,reviews,access_status,attempts,execution_time,failure_reason
```

### Métricas (`ScraperMetrics`)

| Métrica | Fórmula |
|---|---|
| `success_rate` | `successful_requests / total_requests * 100` |
| `failure_rate` | `failed_requests / total_requests * 100` |
| `average_execution_time` | `sum(execution_times) / total_requests` |
| `average_attempts` | `sum(attempts) / total_requests` |

### Reporte (`ReportGenerator`)

Consolida las métricas anteriores en un formato legible para análisis posterior.

---

## Docker (soporte opcional)

```bash
docker compose up --build
```

> **Nota:** en pruebas locales, Chromium en modo headless dentro del contenedor llega a G2 correctamente, pero DataDome no siempre presenta el CAPTCHA de la misma forma que en un entorno local con interfaz (`HEADLESS=false`). No es necesario modificar la lógica funcional solo para Docker — la reproducibilidad vía Docker es soporte adicional, no el requisito central del desafío. La validación funcional principal se recomienda en local con `HEADLESS=false`.

---

## Principios de diseño aplicados

| Principio | Aplicación |
|---|---|
| SRP | Búsqueda, extracción, acceso, retry, persistencia y métricas están separados en componentes distintos. |
| OCP | `CaptchaProvider` permite agregar nuevas implementaciones sin modificar `AccessHandler`. |
| DIP | Las dependencias se inyectan en componentes como `AccessHandler`, en lugar de instanciarse internamente. |
| Alta cohesión | Cada módulo agrupa responsabilidades relacionadas entre sí. |
| Bajo acoplamiento | `G2Scraper` delega los detalles especializados a componentes dedicados. |

---

## Checklist antes de una ejecución funcional

- [ ] Ejecutar tests y confirmar que pasan.
- [ ] Limpiar dataset/reporte de pruebas anteriores.
- [ ] Configurar `SAMPLE_COUNT=100` y `HEADLESS=false`.
- [ ] Ejecutar las 100 muestras sin interrupciones.
- [ ] Revisar `success_rate`, `failure_rate`, `average_execution_time` y `average_attempts`.
- [ ] Revisar el dataset: `sample_id`, URLs, ratings, reviews y estados de acceso.
- [ ] Generar el reporte después de registrar las métricas.
- [ ] Confirmar que `.env`, `.venv`, perfiles de navegador y cachés no se suban al repositorio.