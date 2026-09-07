# Sistema de Scraping Resiliente para G2

Motor de extracción de información de productos desde G2 diseñado para procesar múltiples ejecuciones con alta tasa de éxito e integridad de datos, manteniendo continuidad ante fallos de acceso (bloqueos y CAPTCHA), validando los datos extraídos y generando dataset y métricas para evaluar éxito, estabilidad y latencia.

**Idea central:** detectar → gestionar → reintentar → renovar → validar → registrar → medir → continuar.

---

## Documentación técnica

| Documento | Contenido |
|---|---|
| [`architecture.md`](./docs/architecture.md) | Componentes del sistema, responsabilidades, ciclo de vida de contextos y diagrama de dependencias. |
| [`scraping-flow.md`](./docs/scraping-flow.md) | Secuencia de ejecución paso a paso, desde la configuración hasta el reporte final. |
| [`resilience.md`](./docs/resilience.md) | Detección de acceso, gestión de CAPTCHA, `RetryPolicy`, recuperación y renovación de entornos. |

---

## Requisitos del desafío

| Requisito | Implementación |
|---|---|
| 100 ejecuciones | `ScrapingRunner` + `sample_count` + `sample_id`. |
| Continuidad | Los resultados se procesan y entregan individualmente mediante un flujo asíncrono. |
| Renovación del entorno | Cada 5 muestras se destruye completamente el contexto actual y se crea uno nuevo. |
| Reinicio de sesión | Cada nuevo contexto inicia nuevamente el flujo desde Google antes de continuar con las siguientes muestras. |
| Bloqueos / CAPTCHA | `AccessDetector` + `AccessHandler` + `CaptchaProvider`. |
| Recuperación | `RetryPolicy` + reintentos y backoff exponencial. |
| Rotación de entorno | `BrowserManager` permite utilizar el siguiente proxy configurado cuando el acceso requiere recuperación. |
| Resiliencia ante cambios del DOM | `G2Selectors` + `G2SelectorResolver` utilizan selectores alternativos para reducir la dependencia de una única estructura del DOM. |
| Integridad | `Product` + `ScrapingResult` mediante validación con Pydantic. |
| Validación de producto | `G2ProductValidator` comprueba que la página corresponde al producto esperado. |
| Trazabilidad | `sample_id`, `attempts`, `execution_time`, `access_status` y `failure_reason`. |
| Métricas | `ScraperMetrics`. |
| Dataset | `DatasetWriter`. |
| Reporte | `ReportGenerator`. |
| Reproducibilidad | `Dockerfile` + `docker-compose.yml` + `.dockerignore`. |

Las 100 solicitudes se modelan como 100 ejecuciones independientes. Una ejecución puede generar varios registros de producto (hasta `MAX_PRODUCTS` filas por muestra); `sample_id` conserva la relación entre cada registro y su ejecución.

Las ejecuciones se organizan en bloques de cinco muestras. Al completar cada bloque, el contexto actual se destruye completamente y se crea un nuevo contexto. El nuevo contexto reinicia el flujo de navegación desde Google antes de continuar con las siguientes muestras.

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

## Configuración

Variables de entorno principales definidas en `Settings`:

| Variable | Descripción | Valor de ejemplo |
|---|---|---|
| `SAMPLE_COUNT` | Número de ejecuciones a procesar. | `100` |
| `HEADLESS` | Si el navegador corre sin interfaz gráfica. | `false` |
| `MAX_PRODUCTS` | Máximo de productos extraídos por muestra. | `3` |

* Crea un archivo `.env` en la raíz del proyecto con estas variables antes de ejecutar.
* No subas `.env` al repositorio.

### Archivo de proxies (`proxies.json`)
La rotación de entorno ante un bloqueo de acceso depende de una lista de proxies configurada por separado. `Settings` carga este archivo para que `BrowserManager` pueda seleccionar el siguiente entorno disponible cuando sea necesario.
* Crea un archivo `proxies.json` en la ruta configurada por `Settings` con una lista de proxies disponibles.
* No subas `proxies.json` al repositorio si contiene credenciales o URLs privadas.

---

## Ejecución

```bash
python main.py
```

El proceso:

1. Carga la configuración e inicializa Playwright y los componentes del sistema.
2. Crea el contexto inicial del navegador.
3. Ejecuta `GoogleSearcher` para localizar el dominio objetivo de G2.
4. Ejecuta las muestras configuradas mediante `ScrapingRunner`.
5. Cada muestra se identifica mediante un `sample_id` y su resultado se entrega individualmente para permitir el registro incremental.
6. `G2Scraper` gestiona la navegación, extracción, validación de acceso y recuperación ante errores.
7. Ante CAPTCHA o bloqueo, se aplica la estrategia definida por `RetryPolicy`. Cuando corresponde, `BrowserManager` puede crear un nuevo entorno utilizando el siguiente proxy configurado.
8. Cada cinco muestras, `ScrapingRunner` destruye completamente el contexto actual y crea uno nuevo.
9. Al crear un nuevo contexto, el flujo se reinicia desde Google antes de continuar con las siguientes muestras.
10. Los resultados se registran en el dataset y las métricas se actualizan durante la ejecución.
11. Finalmente, `ReportGenerator` genera el reporte consolidado de métricas.

Ver el detalle completo del flujo en [`scraping-flow.md`](./docs/scraping-flow.md).

---

## Arquitectura

El sistema está organizado en componentes especializados para separar la orquestación, navegación, extracción, gestión de acceso, resiliencia, validación y procesamiento de resultados.

### Componentes principales

| Componente | Responsabilidad |
|---|---|
| `main.py` | Inicialización y composición de dependencias. |
| `ScrapingRunner` | Orquestación de muestras y renovación periódica de contextos. |
| `BrowserManager` | Gestión del navegador, contextos, páginas y proxies. |
| `GoogleSearcher` | Localización del dominio objetivo mediante Google. |
| `G2Scraper` | Coordinación del proceso de scraping y recuperación ante errores. |
| `G2Searcher` | Ejecución de búsquedas dentro de G2. |
| `G2Extractor` | Coordinación de candidatos y extracción de productos. |
| `G2ProductExtractor` | Extracción individual de un producto. |
| `G2ProductDataExtractor` | Extracción y transformación de rating y reviews. |
| `G2ProductValidator` | Validación de que la página corresponde al producto esperado. |
| `G2SelectorResolver` | Resolución mediante selectores alternativos. |
| `G2Selectors` | Centralización de selectores. |
| `G2UIHandler` | Gestión de elementos de interfaz. |
| `AccessDetector` | Detección del estado de acceso. |
| `AccessHandler` | Gestión del resultado de acceso y CAPTCHA. |
| `CaptchaProvider` | Abstracción para mecanismos de CAPTCHA. |
| `RetryPolicy` | Definición de reintentos y tiempos de espera. |
| `Product` | Modelo validado de producto. |
| `ScrapingResult` | Modelo del resultado de una ejecución. |
| `DatasetWriter` | Persistencia del dataset. |
| `ScraperMetrics` | Cálculo de métricas. |
| `ReportGenerator` | Generación del reporte de ejecución. |

Ver el detalle de la arquitectura en [`architecture.md`](./docs/architecture.md).

### Ciclo de vida de los contextos

Las ejecuciones se agrupan en bloques de cinco muestras para evitar mantener un único contexto durante todo el proceso.

```text
Contexto 1
    │
    ├── Google
    ├── Muestra 1
    ├── Muestra 2
    ├── Muestra 3
    ├── Muestra 4
    └── Muestra 5
          │
          ▼
    destroy_context()
          │
          ▼
    Nuevo contexto
          │
          ├── Google
          ├── Muestra 6
          ├── Muestra 7
          ├── Muestra 8
          ├── Muestra 9
          └── Muestra 10
                │
                ▼
          destroy_context()
                │
                ▼
               ...
```

* `BrowserManager.destroy_context()` cierra la página activa, destruye el contexto y limpia las referencias internas.
* El navegador permanece disponible para crear el siguiente contexto.
* Esta separación permite diferenciar entre la renovación de un contexto durante la ejecución y el cierre completo del navegador al finalizar el proceso.

---

## Salidas

### Dataset (`DatasetWriter`)
Archivo CSV con una fila por producto extraído:

```csv
sample_id,product_name,product_url,rating,reviews,access_status,attempts,execution_time,failure_reason
```

* `sample_id` permite identificar la ejecución a la que pertenece cada producto.
* Una ejecución puede generar múltiples filas dependiendo de `MAX_PRODUCTS`.

### Métricas (`ScraperMetrics`)

| Métrica | Fórmula |
|---|---|
| `success_rate` | `successful_requests / total_requests * 100` |
| `failure_rate` | `failed_requests / total_requests * 100` |
| `average_execution_time` | `sum(execution_times) / total_requests` |
| `average_attempts` | `sum(attempts) / total_requests` |

Las métricas se calculan sobre las ejecuciones realizadas y no sobre el número de productos extraídos.

### Reporte (`ReportGenerator`)
Consolida las métricas de ejecución en un formato legible para análisis posterior.

---

## Docker (soporte opcional)

```bash
docker compose up --build
```

> **Nota:** en pruebas locales, Chromium en modo headless dentro del contenedor llega a G2 correctamente, pero DataDome no siempre presenta el CAPTCHA de la misma forma que en un entorno local con interfaz (`HEADLESS=false`). No es necesario modificar la lógica funcional solo para Docker — la reproducibilidad vía Docker es soporte adicional, no el requisito central del desafío. La validación funcional principal se recomienda en local con `HEADLESS=false`.

---

## Principios de diseño

| Principio | Aplicación |
|---|---|
| **SRP** | Búsqueda, extracción, acceso, retry, persistencia y métricas están separados en componentes distintos. |
| **OCP** | `CaptchaProvider` permite agregar nuevas implementaciones sin modificar `AccessHandler`. |
| **DIP** | Las dependencias se inyectan en componentes como `AccessHandler`, en lugar de instanciarse internamente. |
| **Alta cohesión** | Cada módulo agrupa responsabilidades relacionadas entre sí. |
| **Bajo acoplamiento** | `G2Scraper` delega los detalles especializados a componentes dedicados. |

---

## Checklist antes de una ejecución funcional

- [ ] Ejecutar tests y confirmar que pasan.
- [ ] Limpiar dataset/reporte de pruebas anteriores.
- [ ] Configurar `SAMPLE_COUNT=100` y `HEADLESS=false`.
- [ ] Verificar la configuración de los proxies disponibles, si aplica.
- [ ] Ejecutar las 100 muestras sin interrupciones.
- [ ] Verificar la renovación del contexto cada 5 muestras.
- [ ] Verificar que cada nuevo contexto reinicie el flujo desde Google.
- [ ] Revisar `success_rate`, `failure_rate`, `average_execution_time` y `average_attempts`.
- [ ] Revisar el dataset: `sample_id`, URLs, ratings, reviews y estados de acceso.
- [ ] Generar el reporte después de registrar las métricas.
- [ ] Confirmar que `.env`, `proxies.json`, `.venv`, perfiles de navegador y cachés no se suban al repositorio.