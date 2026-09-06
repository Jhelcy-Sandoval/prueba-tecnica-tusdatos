# Estrategia de Resiliencia (G2)

Este documento describe las estrategias implementadas para mantener la continuidad del proceso de extracción ante errores de navegación, verificaciones de acceso, CAPTCHA, bloqueos de acceso y otros fallos recuperables. El objetivo es evitar que un fallo individual interrumpa el conjunto de ejecuciones, permitiendo que el sistema registre el resultado de cada muestra para su posterior análisis.

Este documento complementa la [Arquitectura del Sistema](./architecture.md) y el [Flujo de Scraping](./scraping-flow.md): describe específicamente **cómo** el sistema se recupera cuando algo falla.

---

## 1. Objetivos

La estrategia de resiliencia busca:

- Detectar problemas de acceso durante la navegación.
- Gestionar verificaciones CAPTCHA.
- Reintentar operaciones cuando el error es recuperable.
- Rotar el entorno de ejecución cuando se detecta un bloqueo de acceso.
- Evitar que una ejecución fallida detenga las siguientes.
- Mantener sincronizada la página activa después de una rotación de entorno.
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
| `blocked` | Se detectó un bloqueo de acceso, incluyendo un `hard-block` de DataDome. | Se lanza `AccessBlockedError` y se inicia la estrategia de recuperación. |
| `unknown` | No fue posible determinar el estado de acceso. | Estado no determinado; se trata como condición de acceso a evaluar. |

El resultado de la detección se representa mediante `AccessResult`, lo que permite separar la detección del estado de acceso de las acciones que deben ejecutarse posteriormente.

La detección de DataDome contempla específicamente el indicador de `hard-block` dentro del iframe de verificación. Esto permite diferenciar un bloqueo de acceso de una verificación CAPTCHA.

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
   ├── GoogleCaptchaProvider
   │
   └── G2CaptchaProvider
   │
   ▼
Gestión de CAPTCHA
   │
   ▼
Nueva verificación
   │
   ├── Acceso concedido → continuar
   │
   └── Verificación no resuelta → reintentar
```

`CaptchaProvider` es una abstracción con implementaciones concretas por sitio (`GoogleCaptchaProvider`, `G2CaptchaProvider`). Esto mantiene separadas las particularidades de cada sitio: `AccessHandler` depende del contrato, no de los detalles internos de cada proveedor.

La estrategia de CAPTCHA se utiliza para gestionar estados de acceso y recuperación controlada. No se considera un mecanismo para evadir los sistemas de protección del sitio.

---

## 4. Recuperación ante Bloqueos

Cuando `AccessDetector` identifica un bloqueo de acceso, `AccessHandler` devuelve el estado correspondiente y `G2Scraper` gestiona la excepción `AccessBlockedError`.

El flujo de recuperación es:

```text
Página
   │
   ▼
AccessDetector
   │
   ├── success → continuar
   │
   ├── captcha → AccessHandler → CaptchaProvider
   │
   └── blocked
          │
          ▼
   AccessBlockedError
          │
          ▼
    ¿Quedan intentos?
       │
       ├── No → muestra failed
       │
       └── Sí
            │
            ▼
      Rotación de entorno
            │
            ▼
       BrowserManager
            │
            ├── Cierra contexto actual
            │
            ├── Selecciona siguiente proxy
            │
            ├── Crea nuevo contexto
            │
            └── Crea nueva página
            │
            ▼
        Nuevo intento
```

La ejecución inicial puede utilizar una conexión directa. Ante un bloqueo de acceso, `BrowserManager` permite cambiar al siguiente entorno configurado.

Los proxies se encuentran desacoplados de la lógica principal del scraper y son cargados mediante `Settings` desde el archivo de configuración correspondiente.

El cambio de entorno no garantiza que el siguiente acceso sea exitoso. Cada nuevo entorno vuelve a pasar por el proceso normal de detección de acceso.

---

## 5. Rotación y Ciclo de Vida de la Página

La rotación de entorno implica cerrar el contexto anterior y crear uno nuevo. Esto puede invalidar la instancia de `Page` utilizada por la ejecución anterior.

Para evitar que una muestra posterior intente utilizar una página cerrada, `BrowserManager` mantiene una referencia de la página activa.

El flujo es:

```text
Page A
  │
  ▼
Bloqueo detectado
  │
  ▼
BrowserManager.rotate_proxy()
  │
  ├── Cierra contexto de Page A
  │
  ├── Crea nuevo contexto
  │
  └── Crea Page B
          │
          ▼
BrowserManager.page = Page B
          │
          ▼
ScrapingRunner actualiza
su referencia de página
          │
          ▼
Siguiente muestra utiliza Page B
```

Esta sincronización evita que `ScrapingRunner` conserve una referencia a una página cuyo contexto ya fue cerrado y permite continuar la ejecución después de una rotación de entorno.

---

## 6. Política de Reintentos: `RetryPolicy`

`RetryPolicy` encapsula la estrategia de reintentos para cada muestra.

La política define:

- **Máximo de intentos** por muestra.
- **`base_delay`**: retardo base entre reintentos.
- **Backoff exponencial**: `delay = base_delay * (2 ** attempt)`.

Con `base_delay = 2`, la progresión de espera es:

`2s → 4s → 8s → ...`

Los errores de navegación y las verificaciones CAPTCHA pueden utilizar esta política para determinar cuándo realizar un nuevo intento.

En el caso de un bloqueo de acceso, la recuperación combina la política de reintentos con la rotación de entorno:

```text
Bloqueo
   │
   ▼
¿Quedan intentos?
   │
   ├── No → failed
   │
   └── Sí
        │
        ▼
   Cambiar entorno
        │
        ▼
   Nuevo intento
```

Si se agotan los intentos definidos, la muestra queda registrada como `failed` y `ScrapingRunner` continúa con la siguiente.

Esto evita que una condición externa detenga el conjunto completo de ejecuciones.

### Excepciones manejadas

| Excepción | Origen | Estrategia |
|---|---|---|
| `CaptchaDetectedError` | Verificación CAPTCHA detectada. | Gestión mediante `CaptchaProvider` y reintento cuando corresponda. |
| `AccessBlockedError` | Bloqueo de acceso detectado. | Rotación de entorno y nuevo intento. |
| `NavigationError` | Fallo durante navegación o flujo de búsqueda. | Reintento con backoff exponencial. |

---

## 7. Continuidad entre Muestras

Cada muestra se procesa de forma independiente y cuenta con su propio número de intentos.

Cuando una muestra no puede completarse después de utilizar los mecanismos de recuperación disponibles, el resultado se registra como `failed` y `ScrapingRunner` continúa con la siguiente muestra.

```text
Muestra 1
   │
   ├── Éxito → registrar → Muestra 2
   │
   └── Fallo → recuperar → registrar → Muestra 2
                                      │
                                      ▼
                                  Muestra 3
                                      │
                                      ▼
                                     ...
```

De esta forma, un fallo individual no provoca la terminación anticipada del conjunto de ejecuciones.

---

## 8. Trazabilidad de Fallos

Cada muestra, exitosa o no, se registra con información operacional en `ScrapingResult`:

- `sample_id`: identifica la ejecución que produjo el registro.
- `access_status`: último estado de acceso determinado.
- `attempts`: número de intentos realizados.
- `execution_time`: tiempo total de la muestra.
- `failure_reason`: motivo del fallo, si lo hubo.

Esta información se combina con los datos de negocio (`product_name`, `product_url`, `rating`, `reviews`) en el dataset final, lo que permite analizar estabilidad y calidad de forma conjunta.

---

## 9. Qué es "recuperable" y qué no

Un error se considera **recuperable** cuando corresponde a una condición que puede gestionarse mediante los mecanismos definidos por el sistema, como:

- una verificación CAPTCHA que puede ser gestionada;
- un bloqueo de acceso que permite intentar otro entorno;
- un error de navegación que puede resolverse mediante un nuevo intento.

Se considera **no recuperable** cuando se agotan los intentos definidos en `RetryPolicy` o cuando los mecanismos disponibles no consiguen restablecer el flujo.

En ese punto, la muestra se cierra como `failed` en lugar de seguir reintentando indefinidamente.

Esta distinción permite mantener un equilibrio entre continuidad y control de recursos.

---

## 10. Estrategia Completa de Recuperación

El comportamiento general del sistema puede resumirse de la siguiente manera:

```text
                    ┌───────────────┐
                    │    Página     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │AccessDetector │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
          success        captcha       blocked
              │             │             │
              ▼             ▼             ▼
          continuar    CaptchaProvider  RetryPolicy
                            │             │
                            ▼             ▼
                       verificar     ¿Quedan intentos?
                            │          │          │
                            │          │          └── No → failed
                            │          │
                            │          └── Sí
                            │               │
                            │               ▼
                            │       Rotación de entorno
                            │               │
                            │               ▼
                            │       Nueva página/contexto
                            │               │
                            └───────────────┘
                                    │
                                    ▼
                               Nuevo intento
```

---

## 11. Resumen de la Defensa

| Tema | Respuesta |
|---|---|
| Detección | `AccessDetector` centraliza la identificación de estados `success`, `captcha`, `blocked` y `unknown`. |
| CAPTCHA | `AccessHandler` delega la gestión al `CaptchaProvider` correspondiente al sitio. |
| Bloqueos | `AccessBlockedError` activa una estrategia de recuperación basada en reintentos y rotación de entorno. |
| Rotación | `BrowserManager` cierra el contexto actual y crea uno nuevo utilizando el siguiente entorno configurado. |
| Ciclo de vida | `BrowserManager` mantiene la página activa y `ScrapingRunner` actualiza su referencia después de una rotación. |
| Reintentos | `RetryPolicy` limita los intentos y aplica backoff exponencial cuando corresponde. |
| Continuidad | Una muestra fallida no detiene las siguientes ejecuciones. |
| Trazabilidad | Cada muestra conserva intentos, tiempo, estado de acceso y motivo de fallo. |
| Trade-off | La recuperación no garantiza el éxito; existe un límite de intentos y cada fallo queda registrado. |