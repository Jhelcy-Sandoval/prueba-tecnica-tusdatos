# Estrategia de Resiliencia (G2)

Este documento describe las estrategias implementadas para mantener la continuidad del proceso de extracción ante errores de navegación, verificaciones de acceso, CAPTCHA, bloqueos de acceso, degradación de la sesión de navegación y otros fallos recuperables. El objetivo es evitar que un fallo individual interrumpa el conjunto de ejecuciones, permitiendo que el sistema registre el resultado de cada muestra para su posterior análisis.

Este documento complementa la [Arquitectura del Sistema](./architecture.md) y el [Flujo de Scraping](./scraping-flow.md): describe específicamente **cómo** el sistema se recupera cuando algo falla.

---

## 1. Objetivos

La estrategia de resiliencia busca:

- Detectar problemas de acceso durante la navegación.
- Gestionar verificaciones CAPTCHA.
- Reintentar operaciones cuando el error es recuperable.
- Rotar el entorno de ejecución cuando se detecta un bloqueo de acceso.
- Renovar el contexto de navegación de forma programada, para reducir la acumulación de huella de sesión antes de que ocurra un bloqueo.
- Recuperarse de cambios menores en el DOM mediante selectores alternativos.
- Evitar que una ejecución fallida detenga las siguientes.
- Mantener sincronizada la página activa después de una rotación o renovación de contexto.
- Registrar el estado y motivo de fallo de cada muestra.
- Medir el comportamiento del sistema mediante métricas.
- Mantener la integridad de los datos obtenidos.

---

## 2. Detección del Estado de Acceso

La detección de problemas de acceso está centralizada en `AccessDetector`, que analiza el contenido de la página y determina el estado actual de acceso mediante un `AccessResult` especializado por caso:

| Resultado | Descripción | Comportamiento |
|---|---|---|
| `AccessGranted` | La página está disponible y puede continuar el proceso. | Continúa el flujo normal. |
| `CaptchaRequired` | Se detectó una verificación CAPTCHA. | Se delega a `AccessHandler` → `CaptchaProvider`. |
| `AccessBlocked` | Se detectó un bloqueo de acceso, incluyendo un `hard-block` de DataDome. | Se lanza `AccessBlockedError` y se inicia la estrategia de recuperación. |
| `AccessUnknown` | No fue posible determinar el estado de acceso. | Estado no determinado; se trata como condición de acceso a evaluar. |

Cada resultado implementa su propio comportamiento de validación, lo que permite separar la detección del estado de acceso de las acciones que deben ejecutarse posteriormente, en lugar de centralizar todos los casos mediante condicionales dentro de un único validador.

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

## 5. Renovación Programada de Contextos

Además de la rotación reactiva ante un bloqueo (sección 4), el sistema aplica una **renovación programada** del contexto de navegación cada 5 muestras, independientemente de si se detectó o no un problema de acceso.

```text
Muestra 1 → 2 → 3 → 4 → 5
                          │
                          ▼
              BrowserManager.destroy_context()
                          │
                          ▼
              Crear nuevo contexto
                          │
                          ▼
              Reiniciar desde Google
              (GoogleSearcher.search)
                          │
                          ▼
                Muestra 6 → 10
                          │
                          ▼
                         ...
```

`BrowserManager.destroy_context()` cierra la página activa, cierra el contexto y elimina las referencias internas correspondientes. El navegador en sí permanece disponible — esta operación destruye una **sesión de ejecución**, no el navegador completo.

Al iniciar el nuevo contexto, el flujo **no reutiliza indefinidamente** la URL de G2 obtenida en el bloque anterior: vuelve a pasar por `GoogleSearcher` para localizar el dominio objetivo desde cero. Esto evita mantener un único fingerprint de sesión durante las 100 ejecuciones, reduciendo la probabilidad de acumular suficientes señales como para activar un bloqueo de DataDome antes de que ocurra.

Esta renovación programada y la rotación reactiva ante bloqueo (sección 4) son mecanismos complementarios: uno actúa preventivamente por volumen, el otro reactivamente por detección de bloqueo.

---

## 6. Ciclo de Vida de la Página

Tanto la rotación reactiva (sección 4) como la renovación programada (sección 5) implican cerrar el contexto anterior y crear uno nuevo. Esto puede invalidar la instancia de `Page` utilizada por la ejecución anterior.

Para evitar que una muestra posterior intente utilizar una página cerrada, `BrowserManager` mantiene una referencia de la página activa.

El flujo es:

```text
Page A
  │
  ▼
Bloqueo detectado o renovación programada
  │
  ▼
BrowserManager.destroy_context() / rotate_proxy()
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

Esta sincronización evita que `ScrapingRunner` conserve una referencia a una página cuyo contexto ya fue cerrado, y permite continuar la ejecución tanto después de una rotación por bloqueo como después de una renovación programada.

---

## 7. Resiliencia ante Cambios del DOM

Los selectores utilizados por G2 están centralizados en `G2Selectors`. Cuando existen varias alternativas posibles para localizar un elemento (por ejemplo, el rating o las reviews de un producto), `G2SelectorResolver` prueba los selectores en el orden definido hasta encontrar uno disponible, en lugar de depender de un único selector fijo.

```text
G2Selectors
      │
      ▼
G2SelectorResolver
      │
      ├── Selector principal
      │
      ├── Selector alternativo
      │
      └── Selector de respaldo
```

`G2ProductDataExtractor` utiliza `G2SelectorResolver` para resolver estos selectores al extraer los datos de un producto, y `G2ProductValidator` se apoya en el mismo mecanismo para confirmar que la página corresponde al producto esperado.

**Alcance de esta mitigación:** cubre cambios en los selectores específicos dentro de una página que sí cargó correctamente (por ejemplo, si G2 renombra la clase CSS del rating). **No cubre** condiciones de UI completamente inesperadas donde no hay ningún DOM útil que resolver — como el caso documentado en la sección 12 (`about:blank`), donde no existe ningún selector, alternativo o no, que pueda encontrar el elemento porque la página nunca terminó de cargar el contenido esperado.

---

## 8. Política de Reintentos: `RetryPolicy`

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

## 9. Continuidad entre Muestras

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

## 10. Trazabilidad de Fallos

Cada muestra, exitosa o no, se registra con información operacional en `ScrapingResult`:

- `sample_id`: identifica la ejecución que produjo el registro.
- `access_status`: último estado de acceso determinado.
- `attempts`: número de intentos realizados.
- `execution_time`: tiempo total de la muestra.
- `failure_reason`: motivo del fallo, si lo hubo.

Esta información se combina con los datos de negocio (`product_name`, `product_url`, `rating`, `reviews`) en el dataset final, lo que permite analizar estabilidad y calidad de forma conjunta.

---

## 11. Qué es "recuperable" y qué no

Un error se considera **recuperable** cuando corresponde a una condición que puede gestionarse mediante los mecanismos definidos por el sistema, como:

- una verificación CAPTCHA que puede ser gestionada;
- un bloqueo de acceso que permite intentar otro entorno;
- un cambio de selector dentro de una página que sí cargó, resuelto mediante `G2SelectorResolver`;
- un error de navegación que puede resolverse mediante un nuevo intento.

Se considera **no recuperable** cuando se agotan los intentos definidos en `RetryPolicy`, cuando los mecanismos disponibles no consiguen restablecer el flujo, o cuando la condición de fallo no está cubierta por ninguna de las excepciones tipadas del sistema (ver sección 12).

En el primer caso, la muestra se cierra como `failed` en lugar de seguir reintentando indefinidamente. En el segundo, el proceso puede detenerse por completo — que es la brecha identificada en la sección 12.

Esta distinción permite mantener un equilibrio entre continuidad y control de recursos, aunque también deja claro que "resiliente" no significa "cubre absolutamente cualquier fallo posible".

---

## 12. Excepciones No Cubiertas (Gap Identificado)

Durante una ejecución real se presentó una condición que las excepciones tipadas actuales (`CaptchaDetectedError`, `AccessBlockedError`, `NavigationError`) no cubren: el navegador cargó una pantalla en blanco (`about:blank`) sin el elemento de búsqueda esperado. Como no existe un manejador específico para este caso, el error no se clasificó como una muestra fallida recuperable — interrumpió el proceso completo en lugar de registrarse y continuar con la siguiente muestra.

Esto representa una brecha real entre el diseño de resiliencia (secciones 1-11) y su cobertura efectiva: el sistema está preparado para recuperarse de los escenarios anticipados (CAPTCHA, bloqueo, cambios de selector dentro de una página cargada, timeouts de navegación), pero no de condiciones de UI completamente inesperadas fuera de ese catálogo, donde no hay ningún DOM útil sobre el cual `G2SelectorResolver` pueda resolver una alternativa.

**Corrección pendiente:** envolver el ciclo principal de `ScrapingRunner` en un manejo de excepción genérica que capture cualquier error no anticipado, lo registre con `access_status="failed"` y un `failure_reason` descriptivo, y continúe con la siguiente muestra — en lugar de propagar el error hasta detener el proceso completo. Esto extendería la garantía de continuidad (sección 9) para cubrir también las condiciones no anticipadas, no solo las excepciones tipadas actuales.

---

## 13. Resumen de la Defensa

| Tema | Respuesta |
|---|---|
| Detección | `AccessDetector` centraliza la identificación de `AccessGranted`, `CaptchaRequired`, `AccessBlocked` y `AccessUnknown`. |
| CAPTCHA | `AccessHandler` delega la gestión al `CaptchaProvider` correspondiente al sitio. |
| Bloqueos | `AccessBlockedError` activa una estrategia de recuperación basada en reintentos y rotación de entorno. |
| Renovación programada | `BrowserManager` renueva el contexto cada 5 muestras y reinicia desde Google, independientemente de si hubo bloqueo. |
| Cambios de DOM | `G2SelectorResolver` prueba selectores alternativos dentro de una página cargada; no cubre pantallas sin contenido útil. |
| Ciclo de vida | `BrowserManager` mantiene la página activa y `ScrapingRunner` actualiza su referencia tras cada rotación o renovación. |
| Reintentos | `RetryPolicy` limita los intentos y aplica backoff exponencial cuando corresponde. |
| Continuidad | Una muestra fallida no detiene las siguientes ejecuciones — salvo la brecha de excepciones no tipadas (sección 12). |
| Trazabilidad | Cada muestra conserva intentos, tiempo, estado de acceso y motivo de fallo. |
| Trade-off | La recuperación no garantiza el éxito; existe un límite de intentos, una brecha conocida de cobertura, y cada fallo queda registrado. |