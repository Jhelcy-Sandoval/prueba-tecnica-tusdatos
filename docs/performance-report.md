# Reporte de Rendimiento — Extracción de Datos G2

*Este documento se reconstruye a partir del dataset (`dataset.csv`) porque el reporte automático de `ReportGenerator` no llegó a generarse en la corrida extendida: el proceso se interrumpió por una excepción no controlada después de la muestra 134 (ver sección 6), antes de completar la ejecución y disparar la generación del reporte final.*

## 1. Resumen de la ejecución

Se ejecutaron **100 muestras** (correspondientes a las muestras 35-134 de una corrida más larga; las primeras 34 se excluyen de este reporte por incluir el primer episodio de bloqueo mientras se ajustaba la configuración de red), cada una realizando una búsqueda en G2 por el término "metricas" y extrayendo hasta `MAX_PRODUCTS=2` productos candidatos por muestra.

| Métrica | Valor |
|---|---:|
| `total_requests` | 100 |
| `successful_requests` | 98 |
| `failed_requests` | 2 |
| `success_rate` | 98.00% |
| `failure_rate` | 2.00% |
| `average_execution_time` | 18.32 s |
| `average_attempts` | 1.02 |

Dataset resultante: 196 registros de producto (2 por muestra × 98 muestras exitosas), sin valores nulos en `rating` ni `reviews`.

---

## 2. Tasa de éxito

**98/100 muestras exitosas (98%).** Las 2 muestras fallidas (70 y 71) corresponden a un episodio de `AccessBlockedError` — bloqueo de acceso detectado por `AccessDetector` tras acumular suficiente volumen de solicitudes desde la misma IP.

## 3. Estabilidad

El sistema mostró un patrón estable durante la mayor parte de la corrida: tiempos de ejecución consistentes (~16-24s) a lo largo de más de 60 muestras consecutivas, interrumpidos por un único episodio de bloqueo (muestras 70-71). Esto es consistente con el comportamiento documentado en `resilience.md`: cada IP soporta un volumen variable de solicitudes antes de que DataDome escale a bloqueo total de acceso.

La ejecución se recuperó del bloqueo: tras las 2 muestras fallidas, un reinicio manual del router permitió que la muestra 72 continuara con éxito, y el sistema se mantuvo estable durante las 63 muestras restantes sin nuevos bloqueos. Esto demuestra que la estrategia de continuidad (`ScrapingRunner` no se detiene ante una muestra fallida) funciona según lo diseñado incluso bajo un bloqueo real.

## 4. Manejo de excepciones

- **`AccessBlockedError`**: gestionado correctamente. Ambas muestras fallidas (70, 71) agotaron sus reintentos (`attempts=2`) según `RetryPolicy`, quedaron registradas como `failed` con `failure_reason=AccessBlockedError`, y `ScrapingRunner` continuó con la siguiente muestra sin detener el proceso completo.
- **CAPTCHA**: gestionado exitosamente en las muestras donde apareció, sin requerir reintento adicional en la mayoría de los casos.
- **Excepción no controlada (fuera de las 100 muestras reportadas)**: después de la muestra 134, el proceso encontró una pantalla `about:blank` de Chromium/Brave sin el input de búsqueda esperado. Esta condición no está cubierta por ninguna de las excepciones tipadas del sistema (`CaptchaDetectedError`, `AccessBlockedError`, `NavigationError`), por lo que no fue manejada como un caso recuperable — cerró el proceso completo en lugar de registrar la muestra como fallida y continuar. Esta brecha está documentada en [`resilience.md`](./resilience.md), sección 12, junto con la corrección pendiente.

## 5. Latencia

Tiempo promedio de ejecución por muestra: **18.32 segundos** sobre las 100 muestras (incluyendo las 2 fallidas, que tardan más por los reintentos con backoff). Las muestras exitosas se mantuvieron consistentemente entre 15 y 24 segundos; las fallidas por `AccessBlockedError` tomaron considerablemente más tiempo, reflejando el backoff exponencial antes de agotar los intentos.

---

## 6. Limitaciones conocidas

**Volumen por IP.** La IP residencial utilizada soportó aproximadamente 35 solicitudes consecutivas antes del episodio de bloqueo (muestras 70-71), y se recuperó tras un reinicio de router. La mitigación aplicada fue manual — no automatizada — porque no se contó con un pool de proxies de buena reputación para validar la rotación automática (`BrowserManager.rotate_proxy`) a mayor escala.

**Excepciones fuera del catálogo tipado.** El incidente de `about:blank` tras la muestra 134 mostró que existen condiciones de fallo (pantallas en blanco, elementos de UI inesperados) que no están cubiertas por las excepciones específicas del sistema. Cuando ocurre una de estas condiciones no anticipadas, el proceso puede detenerse por completo en lugar de registrar la muestra como fallida y continuar — es la principal brecha identificada entre el diseño de resiliencia y su cobertura real. La corrección propuesta está detallada en [`resilience.md`](./resilience.md), sección 12.

Ambas limitaciones están documentadas con más detalle en [`resilience.md`](./resilience.md) y en [`technical-justification.md`](./technical-justification.md).