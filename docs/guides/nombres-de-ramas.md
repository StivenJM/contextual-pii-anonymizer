# Cómo nombrar ramas de trabajo

Esta guía define cómo nombrar ramas para que cualquier persona pueda reconocer el tipo de cambio, el área principal afectada y el resultado esperado sin inspeccionar su contenido.

## Formato

Usa siempre esta estructura:

```text
<tipo>/<alcance>/<resultado>
```

El resultado debe escribirse en inglés, en minúsculas y con palabras separadas por guiones:

```text
feat/api/add-protection-rules
fix/inference/normalize-model-offsets
experiment/ml/compare-ner-models
```

## Tipos de cambio

| Tipo | Uso |
|---|---|
| `feat` | Incorpora una capacidad nueva. |
| `fix` | Corrige un comportamiento defectuoso. |
| `refactor` | Reorganiza una implementación sin cambiar su comportamiento. |
| `test` | Añade o corrige pruebas sin modificar el comportamiento productivo. |
| `docs` | Actualiza documentación. |
| `build` | Modifica empaquetado, contenedores o despliegue. |
| `chore` | Realiza mantenimiento sin alterar capacidades del sistema. |
| `experiment` | Ejecuta una prueba de concepto o comparación de modelos. |
| `data` | Prepara, transforma o versiona datasets. |

`experiment` y `data` distinguen trabajo exploratorio de ML de una capacidad productiva. Una prueba de concepto no debe presentarse como `feat` hasta que tenga un comportamiento integrado y verificable.

## Alcances del monorepo

| Alcance | Responsabilidad principal |
|---|---|
| `api` | API FastAPI, casos de uso, reglas de protección y persistencia. |
| `inference` | Servicio BentoML, catálogo y ejecución de modelos. |
| `ml` | Datos, entrenamiento, evaluación y experimentos de modelos. |
| `infra` | Docker Compose, imágenes, despliegue y recursos operativos. |
| `platform` | Comportamiento que necesita cambios coordinados e inseparables en varios servicios. |
| `docs` | Organización y mantenimiento transversal de la documentación. |
| `repo` | Configuración, automatización o herramientas compartidas por todo el repositorio. |

El alcance representa el área dueña del resultado, no todos los archivos modificados. Una rama `feat/api/add-audit-records` puede incluir sus pruebas y documentación sin cambiar de alcance.

Para documentación específica de un componente, conserva ese componente como alcance:

```text
docs/api/explain-database-startup
docs/inference/document-model-registration
```

Usa `docs` como alcance cuando el cambio afecta la organización documental en sí:

```text
chore/docs/fix-navigation-links
```

## Procedimiento

### 1. Define un único resultado

Describe qué debe quedar resuelto al integrar la rama. Si el nombre necesita enumerar varios resultados independientes, divide el trabajo.

### 2. Selecciona el tipo

Elige el tipo por la intención principal del cambio. No uses `chore` como categoría genérica cuando `feat`, `fix`, `experiment` o `data` expresen mejor el propósito.

### 3. Identifica el alcance dueño

Selecciona el componente responsable del comportamiento. Los cambios auxiliares en pruebas, documentación o configuración no convierten automáticamente la rama en transversal.

Usa `platform` solamente cuando el resultado no pueda entregarse correctamente modificando un único componente. No combines alcances en nombres como `api-inference-ml`.

### 4. Escribe un resultado breve

Usa una frase verbal concreta de entre dos y cinco palabras. Evita nombres que solo describan actividad o estado temporal.

| Evita | Prefiere |
|---|---|
| `temp1` | `feat/api/add-protection-rules` |
| `tests` | `test/inference/cover-model-catalog` |
| `pipeline-poc` | `experiment/ml/evaluate-training-pipeline` |
| `changes` | `refactor/api/split-policy-engine` |

### 5. Crea la rama desde `develop`

Actualiza la rama de integración antes de comenzar:

```powershell
git switch develop
git pull --ff-only
git switch -c <tipo>/<alcance>/<resultado>
```

Las ramas de trabajo se integran en `develop`. `main` representa versiones estables y no es la base habitual para cambios de desarrollo.

## Cambios transversales

Un cambio que toca varias carpetas no es necesariamente transversal.

- Usa el alcance principal cuando los demás cambios solo habilitan o verifican el resultado de ese componente.
- Usa `platform` cuando API e inferencia, u otros componentes, deban cambiar juntos para entregar un único comportamiento.
- Crea ramas separadas cuando cada componente pueda revisarse, probarse e integrarse de forma independiente.

Ejemplos:

```text
feat/platform/connect-api-inference
build/infra/add-gpu-runtime
chore/repo/update-python-tooling
```

## Reglas obligatorias

- Mantén una sola finalidad revisable por rama.
- Usa únicamente minúsculas, caracteres ASCII y guiones.
- Conserva el formato `tipo/alcance/resultado` durante todo el proyecto.
- Incluye en la misma rama las pruebas y la documentación necesarias para verificar su resultado.
- Evita nombres personales, números temporales y estados como `wip`, `temp` o `final`.
- Elimina la rama después de integrarla si ya no contiene trabajo activo.

## Lista de verificación

Antes de publicar una rama, confirma:

- [ ] El tipo explica la intención principal.
- [ ] El alcance identifica al dueño del cambio.
- [ ] El resultado permite anticipar qué quedará resuelto.
- [ ] La rama no mezcla resultados independientes.
- [ ] El nombre usa minúsculas y `kebab-case`.
- [ ] Las pruebas y la documentación relacionadas forman parte de la misma unidad de trabajo.
