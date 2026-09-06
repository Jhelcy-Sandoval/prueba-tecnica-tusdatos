# Reporte de Rendimiento — Extracción de Datos G2

*Este documento interpreta y contextualiza las métricas generadas automáticamente por `ReportGenerator` [`../reports/execution_report.md`](../reports/execution_report.md), salida directa del sistema tras la ejecución. El objetivo aquí es explicar qué significan esos números y documentar las condiciones bajo las que se obtuvieron.*

## 1. Resumen de la ejecución

Se ejecutaron **10 muestras** completas de forma consecutiva, cada una realizando una búsqueda en G2 por el término "metricas" y extrayendo hasta 3 productos candidatos por muestra.

| Métrica | Valor |
|---|---|
| `total_requests` | 10 |
| `successful_requests` | 10 |
| `failed_requests` | 0 |
| `success_rate` | 100.0% |
| `failure_rate` | 0.0% |
| `average_execution_time` | 17.22 s |
| `average_attempts` | 1.0 |

Dataset resultante: 30 registros de producto (3 por muestra × 10 muestras), sin valores nulos en `rating` ni `reviews`.

---

## 2. Tasa de éxito

**10/10 muestras exitosas (100%).** En esta tanda no se presentó ningún bloqueo de acceso (`blocked`); solo se detectó un CAPTCHA en la muestra 1, que fue gestionado correctamente por `CaptchaProvider` sin necesidad de reintento (`attempts=1` en todas las muestras).

Es importante contextualizar esta tasa: en tandas anteriores de mayor volumen (18+ muestras consecutivas desde la misma IP), el sistema fue bloqueado por completo por DataDome antes de completar el objetivo de 100 ejecuciones. El 100% de éxito reportado aquí corresponde a una tanda de tamaño reducido, diseñada para no agotar la IP disponible y así poder validar la corrección del pipeline completo (búsqueda → extracción → validación → persistencia) sin ruido.

## 3. Estabilidad

Dentro de esta tanda de 10 muestras, el comportamiento fue estable: mismo número de productos por muestra (3), mismo patrón de intentos (1 en todos los casos), y sin degradación progresiva en la calidad de los datos extraídos a medida que avanzaban las muestras.

A mayor escala, la estabilidad observada en pruebas previas muestra un patrón distinto: el sistema se mantiene estable durante aproximadamente 15-18 muestras consecutivas por IP, tras lo cual DataDome escala la respuesta de verificación de CAPTCHA a bloqueo total de acceso (`AccessBlockedError`), afectando incluso a otros dispositivos conectados a la misma red pública. Este es el principal factor de inestabilidad del sistema a volúmenes mayores, no la lógica de extracción en sí.

## 4. Manejo de excepciones

- **CAPTCHA (`CaptchaDetectedError`)**: gestionado exitosamente en la muestra 1 mediante `AccessHandler` → `CaptchaProvider`, sin requerir reintento adicional.
- **Timing de extracción tras CAPTCHA**: se corrigió un defecto detectado en pruebas previas donde, inmediatamente después de resolver un CAPTCHA, el extractor leía el DOM antes de que el rating y las reviews terminaran de renderizarse, generando valores `None`. La corrección reemplazó la verificación por conteo (`.count()`, que no espera renderizado) por una espera explícita sobre el elemento (`wait_for`), eliminando por completo los valores nulos en esta tanda.
- **Bloqueo de acceso (`AccessBlockedError`)**: no se presentó en esta tanda de 10 muestras. En pruebas de mayor volumen, este es el punto de falla dominante: una vez agotados los intentos de `RetryPolicy` y la rotación de proxy disponible, la muestra se registra como `failed` con su `failure_reason`, y `ScrapingRunner` continúa sin detener el resto de la ejecución — el comportamiento de continuidad funciona según lo diseñado incluso bajo esta condición.

## 5. Latencia

Tiempo promedio de ejecución por muestra: **17.22 segundos**, con un rango observado entre ~14.2s y ~27.2s. La muestra más lenta (27.15s) corresponde a la primera ejecución, que incluyó la resolución del CAPTCHA; las muestras posteriores sin verificación adicional se mantuvieron consistentemente entre 14 y 21 segundos.

---

## 6. Limitación conocida: volumen máximo por IP

El objetivo de la prueba especifica 100 ejecuciones. La limitación principal para alcanzar ese volumen no fue la lógica del sistema, sino la disponibilidad de direcciones IP no bloqueadas:

- Cada IP residencial utilizada (red doméstica) soporta de forma consistente entre 15 y 18 muestras antes de que DataDome escale a un bloqueo total de acceso — no solo de la sesión del scraper, sino de la IP pública completa, afectando incluso el acceso manual desde el navegador y desde otros dispositivos en la misma red.
- El sistema cuenta con rotación de entorno (`BrowserManager.rotate_proxy`) para este escenario, pero su efectividad depende de tener un pool de proxies con buena reputación disponible. No se contó con presupuesto para proxies residenciales de pago, que son los recomendados para sitios con protección DataDome de este nivel.
- Como mitigación sin costo, se validó el sistema en tandas más pequeñas (10 muestras) usando redes distintas entre tandas, confirmando que el pipeline de extracción, validación y persistencia es correcto y estable dentro del límite que cada IP permite.

Esta limitación está documentada en detalle en [`resilience.md`](./resilience.md), sección 4 (Recuperación ante Bloqueos).