# Justificación de la Estrategia Técnica

*Documento breve requerido por la prueba: por qué se eligió esta estrategia para garantizar la durabilidad de la solución. Para el detalle completo de componentes y flujo, ver [`architecture.md`](./architecture.md), [`scraping-flow.md`](./scraping-flow.md) y [`resilience.md`](./resilience.md).*

---

## El problema central

Un scraper contra un sitio protegido por DataDome no puede asumir que cada solicitud va a tener éxito. La pregunta de diseño no es "¿cómo evito que me bloqueen?" (no es controlable de forma determinística), sino **"¿cómo hago que un bloqueo individual no comprometa las 99 solicitudes restantes?"**. Esa pregunta guio cada decisión de arquitectura.

## Por qué se separó detección, gestión y reintento en componentes distintos

`AccessDetector`, `AccessHandler`, `CaptchaProvider` y `RetryPolicy` son componentes independientes en lugar de lógica mezclada dentro del extractor, por dos razones prácticas:

- **DataDome cambia de comportamiento** (a veces presenta CAPTCHA, a veces bloquea directo, a veces no reacciona). Si esa lógica estuviera embebida en `G2Extractor`, cada ajuste a la detección de acceso implicaría tocar código de extracción de datos, aumentando el riesgo de romper algo que ya funcionaba.
- **Permite evolucionar cada pieza por separado**: se puede cambiar el proveedor de CAPTCHA, ajustar el número de reintentos, o agregar un nuevo estado de acceso sin que el resto del sistema se entere.

## Por qué backoff exponencial y no reintento inmediato

Reintentar inmediatamente después de un bloqueo agrava el problema: es el mismo patrón de tráfico que causó la detección en primer lugar. El backoff (`2s → 4s → 8s...`) da tiempo a que una condición temporal (rate-limit, verificación puntual) se disipe antes del siguiente intento, en lugar de insistir contra una defensa que ya está activa.

## Por qué continuar en vez de detener todo el proceso

El requisito de negocio es "100 muestras con alta tasa de éxito e integridad", no "100 muestras perfectas sin ninguna falla". Diseñar para que una muestra fallida se registre como `failed` y el proceso continúe con la siguiente es lo que hace posible reportar métricas reales de estabilidad (`success_rate`, `failure_rate`) en lugar de un proceso que se cae por completo ante el primer error — que sería mucho más frágil y, paradójicamente, más difícil de evaluar.

## Por qué rotación de entorno (proxy) en vez de solo reintentar en la misma IP

Un `AccessBlockedError` en la misma IP no es una condición temporal como un CAPTCHA — es una decisión del sitio de dejar de servir esa IP. Reintentar sin cambiar de entorno no tiene sentido en ese caso específico; por eso `BrowserManager` puede rotar a un nuevo contexto de navegación con un proxy distinto, tratando el bloqueo de IP como una categoría de fallo distinta a un CAPTCHA o un timeout de navegación.

**Limitación honesta de esta parte de la estrategia**: la rotación de entorno es tan efectiva como la calidad del pool de proxies disponible. En esta implementación, el pool disponible fue de proxies gratuitos/de baja reputación, que DataDome bloquea con la misma facilidad que la IP original tras un volumen similar de solicitudes. La arquitectura para rotar está correctamente implementada y separada del resto del sistema (cumple el objetivo de diseño); el resultado a escala de 100 ejecuciones depende de un recurso externo (proxies residenciales de pago) que no formaba parte del alcance posible de esta prueba. Ver el diagnóstico completo en [`performance-report.md`](./performance-report.md).

## Por qué validación con Pydantic en el modelo `Product`

Los datos extraídos vienen de HTML que puede cambiar de formato (`"(7,964)"` vs `"7964"`, ratings como texto). Validar y normalizar en el punto de entrada del modelo, en lugar de confiar en que el HTML siempre viene limpio, es lo que evita que un formato inesperado se propague como ruido hasta el dataset final — que es justo uno de los criterios de evaluación de esta prueba.