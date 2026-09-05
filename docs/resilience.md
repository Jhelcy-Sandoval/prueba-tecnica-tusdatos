# Estrategia de Resiliencia (G2)

Este documento describe las estrategias implementadas para mantener la continuidad del proceso de extracción ante errores de navegación, verificaciones de acceso, CAPTCHA y otros fallos recuperables. El objetivo es evitar que un fallo individual interrumpa el conjunto de ejecuciones, permitiendo que el sistema registre el resultado de cada muestra para su posterior análisis.

Este documento complementa la [Arquitectura del Sistema](./arquitectura.md) y el [Flujo de Scraping](./scraping_flow.md): describe específicamente *cómo* el sistema se recupera cuando algo falla.

---

## 1. Objetivos

La estrategia de resiliencia busca:

- Detectar problemas de acceso durante la navegación.
- Gestionar verificaciones CAPTCHA.
- Reintentar operaciones cuando el error es recuperable.
- Evitar que una ejecución fallida detenga las siguientes.
- Registrar el estado y motivo de fallo de cada muestra.
- Medir el comportamiento del sistema mediante métricas.
- Mantener la integridad de los datos obtenidos.

---

## 2. Detección del Estado de Acceso

La detección de problemas de acceso está centralizada en `AccessDetector`, que analiza el contenido de la página y determina el estado actual de acceso.

| Estado | Descripción | Comportamiento |
|---|---|---|
| `success` | La página está disponible y puede continuar el proceso. | Continúa el flujo normal. |
| `captcha` | Se detectó una verificación CAPTCHA. | Se delega a `AccessHandler` → `CaptchaProvider`. |
| `blocked` | Se detectó un bloqueo de acceso. | Se lanza `AccessBlockedError`; entra `RetryPolicy`. |
| `unknown` | No fue posible determinar el estado de acceso. | Estado no determinado; se trata como condición de acceso a evaluar. |

El resultado de la detección se representa mediante `AccessResult`, lo que permite separar la detección del estado de acceso de las acciones que deben ejecutarse posteriormente.

---

## 3. Gestión de CAPTCHA

Cuando `AccessDetector` determina que existe un CAPTCHA, `AccessHandler` delega su gestión al `CaptchaProvider` correspondiente.

```text
Página
   │
   ▼
AccessDetector
   │
   ▼
CAPTCHA detectado
   │
   ▼
AccessHandler
   │
   ▼
CaptchaProvider
   │
   ▼
Gestión de CAPTCHA
   │
   ▼
Nueva verificación
   │
   ├── Acceso concedido → continuar
   │
   └── CAPTCHA continúa → reintentar
```

`CaptchaProvider` es una abstracción con implementaciones concretas por sitio (`GoogleCaptchaProvider`, `G2CaptchaProvider`). Esto mantiene separadas las particularidades de cada sitio: `AccessHandler` depende del contrato, no de los detalles internos de cada proveedor. El objetivo es gestionar estados de acceso y recuperación controlada — no presentar el sistema como un mecanismo de bypass.

---

## 4. Recuperación ante Bloqueos: `RetryPolicy`

Cuando el estado es `blocked`, el sistema lanza una excepción y `RetryPolicy` decide si reintentar.

```text
Página → AccessDetector
 ├── success  → continuar
 ├── captcha  → AccessHandler → CaptchaProvider → verificar
 ├── blocked  → excepción → RetryPolicy → retry
 └── failed   → siguiente muestra (intentos agotados)
```

`RetryPolicy` encapsula:

- **Máximo de intentos** por muestra.
- **`base_delay`**: retardo base entre reintentos.
- **Backoff exponencial**: `delay = base_delay * (2 ** attempt)`.

Con `base_delay = 2`, la progresión de espera es: `2s → 4s → 8s → ...`

Si se agotan los intentos, la muestra queda registrada como `failed` y `ScrapingRunner` continúa con la siguiente. Esto evita que una sola condición externa detenga el conjunto completo de ejecuciones.

**Excepciones manejadas:**

| Excepción | Origen |
|---|---|
| `CaptchaDetectedError` | Verificación CAPTCHA detectada. |
| `AccessBlockedError` | Bloqueo de acceso detectado. |
| `NavigationError` | Fallo de navegación (timeout, error de red, etc.). |

---

## 5. Trazabilidad de Fallos

Cada muestra, exitosa o no, se registra con la siguiente información operacional en `ScrapingResult`:

- `sample_id`: identifica la ejecución que produjo el registro.
- `access_status`: último estado de acceso determinado.
- `attempts`: número de intentos realizados.
- `execution_time`: tiempo total de la muestra.
- `failure_reason`: motivo del fallo, si lo hubo.

Esta información se combina con los datos de negocio (`product_name`, `product_url`, `rating`, `reviews`) en el dataset final, lo que permite analizar estabilidad y calidad de forma conjunta.

---

## 6. Qué es "recuperable" y qué no

Un error se considera **recuperable** cuando corresponde a una condición temporal de acceso (`captcha`, `blocked`) que puede resolverse reintentando o gestionando la verificación. Se considera **no recuperable** cuando se agotan los intentos definidos en `RetryPolicy` — en ese punto, la muestra se cierra como `failed` en lugar de seguir reintentando indefinidamente.

Esta distinción es la que permite cumplir el objetivo central: **una condición externa (CAPTCHA, bloqueo temporal) no debe detener el conjunto de 100 ejecuciones**, pero tampoco se asume que todo error se puede resolver reintentando para siempre.

---

## 7. Resumen de la Defensa

| Tema | Respuesta |
|---|---|
| Resiliencia | Se detecta el estado de acceso, se gestiona CAPTCHA mediante una abstracción y se aplican excepciones + backoff exponencial. |
| Continuidad | Cada muestra es independiente; una falla no detiene las siguientes. |
| Trade-off | No todos los errores se recuperan; existe un límite de intentos y se registra el resultado final. |