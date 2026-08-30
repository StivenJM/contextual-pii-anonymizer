# Bosquejo MVP: API funcional del modelo

Este documento define el alcance mínimo para tener una API funcional en pocas horas. La visión final sigue siendo FastAPI como backend del middleware y BentoML como servicio especializado de inferencia, pero este primer corte prioriza demostrar que la API puede recibir texto, ejecutar un modelo o detector inicial y devolver entidades estructuradas.

## Objetivo inmediato

Construir una API básica que permita probar el flujo principal:

1. recibir texto desde un cliente;
2. validar que el texto sea procesable;
3. ejecutar detección de PII con el modelo disponible;
4. devolver entidades detectadas;
5. devolver una versión anonimizada simple del texto.

El objetivo no es implementar todavía todo el middleware experimental, sino dejar una base real sobre la que después se puedan agregar sesiones, métricas, políticas, persistencia y proxy hacia LLM.

## Alcance del MVP de horas

| Área | Decisión |
|---|---|
| Backend | FastAPI |
| Inferencia | Con BentoML |
| BentoML | Debe estar implementado |
| Persistencia | No incluida |
| Autenticación | No incluida |
| Sesiones experimentales | No incluidas |
| Proxy hacia LLM | No incluido |
| Métricas avanzadas | No incluidas |

## Endpoints mínimos

### GET /

Devuelve el estado general de la API.

Respuesta esperada:

```json
{
  "message": "Contextual PII Anonymizer API",
  "version": "1.0.0",
  "status": "active"
}
```

### GET /api/health

Permite verificar que la API responde.

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "contextual-pii-anonymizer-api",
  "version": "1.0.0"
}
```

### POST /api/analyze

Recibe texto y devuelve las entidades detectadas sin modificar el texto.

Request:

```json
{
  "text": "Juan Perez tiene el correo juan@example.com"
}
```

Response:

```json
{
  "text": "Juan Perez tiene el correo juan@example.com",
  "entities": [
    {
      "type": "PER",
      "text": "Juan Perez",
      "start": 0,
      "end": 10,
      "confidence": 0.95,
      "source": "model"
    },
    {
      "type": "EMAIL",
      "text": "juan@example.com",
      "start": 28,
      "end": 44,
      "confidence": 1.0,
      "source": "regex"
    }
  ],
  "model_version": "mvp"
}
```

### POST /api/deidentify

Recibe texto, detecta entidades y devuelve una versión anonimizada simple.

Request:

```json
{
  "text": "Juan Perez tiene el correo juan@example.com"
}
```

Response:

```json
{
  "original_text": "Juan Perez tiene el correo juan@example.com",
  "deidentified_text": "<PERSON> tiene el correo <EMAIL>",
  "entities": [
    {
      "type": "PER",
      "text": "Juan Perez",
      "start": 0,
      "end": 10,
      "replacement": "<PERSON>",
      "confidence": 0.95,
      "source": "model"
    },
    {
      "type": "EMAIL",
      "text": "juan@example.com",
      "start": 28,
      "end": 44,
      "replacement": "<EMAIL>",
      "confidence": 1.0,
      "source": "regex"
    }
  ],
  "model_version": "mvp"
}
```

## Taxonomía mínima

Para este primer corte solo se necesita soportar la taxonomía MVP:

| Código | Entidad | Reemplazo |
|---|---|---|
| PER | Persona | `<PERSON>` |
| ID | Cédula ecuatoriana | `<ID>` |
| PH | Teléfono | `<PHONE>` |
| EMAIL | Correo electrónico | `<EMAIL>` |

## Reglas mínimas de validación

La API debe rechazar:

- texto vacío;
- texto que no sea string;
- texto excesivamente largo para el primer prototipo.

Respuesta de error sugerida:

```json
{
  "message": "Invalid request"
}
```

## Flujo interno mínimo

```text
Cliente
  ↓
FastAPI route
  ↓
Controller
  ↓
Use case
  ↓
Detector inicial del modelo
  ↓
Respuesta estructurada
```

## Prioridad de implementación

1. Mantener funcionando `GET /` y `GET /api/health`.
2. Crear DTOs de request/response para análisis y desidentificación.
3. Crear `POST /api/analyze`.
4. Crear `POST /api/deidentify`.
5. Integrar el modelo disponible o un adaptador mínimo que permita reemplazarlo después.
6. Agregar regex para EMAIL, ID y PH si el modelo no los cubre bien.
7. Verificar con ejemplos manuales desde Swagger o `curl`.

## Fuera de alcance por ahora

No implementar todavía:

- sesiones experimentales;
- participantes;
- autenticación;
- base de datos;
- exportación de resultados;
- métricas de aceptación;
- proxy hacia LLM;
- administración de modelos;
- UI o extensión del navegador.

Estas partes pertenecen a la arquitectura final, pero no son necesarias para demostrar una API funcional del modelo.

## Criterio de terminado

El MVP queda listo cuando:

- la API arranca localmente desde `api/`;
- `GET /api/health` responde correctamente;
- `POST /api/analyze` devuelve entidades estructuradas;
- `POST /api/deidentify` devuelve texto anonimizado;
- la respuesta incluye `model_version`;
- existe al menos un ejemplo exitoso con persona, correo, teléfono o cédula.

## Siguiente paso después del MVP

Cuando este flujo funcione, el siguiente paso será separar la inferencia en BentoML o en un adaptador interno más claro, según el costo real de cargar y ejecutar el modelo.
