# Cómo verificar la calidad de código con Ruff

Esta guía explica cómo ejecutar el linting y el formateo del código Python de la API. Ruff está disponible como dependencia de desarrollo administrada por `uv`, por lo que no necesita una instalación global.

Los comandos de esta guía se ejecutan desde el directorio `api/`:

```bash
cd api
```

## Alcance actual

La configuración vigente cubre la API. Los demás proyectos del monorepo deben incorporar su propia dependencia y configuración antes de adoptar este procedimiento.

Al ejecutar Ruff puedes decidir si revisas toda la API o una ruta concreta. No es opcional ejecutar tanto el linter como el formatter antes de integrar cambios: cada herramienta comprueba una responsabilidad distinta.

## Configuración vigente

Ruff aplica este perfil a la API:

| Opción | Valor |
|---|---|
| Versión objetivo de Python | Python 3.14 |
| Longitud de línea | 88 caracteres |
| Comillas | Dobles |
| Indentación | Espacios |
| Reglas de linting | `E`, `F`, `I`, `B`, `UP`, `FAST`, `ASYNC`, `SIM`, `C4`, `PIE`, `RET`, `RUF` y `PT` |

El archivo de configuración es la fuente de verdad. No pases opciones distintas en la línea de comandos para evitar una regla; cambia la configuración solamente cuando la nueva decisión deba aplicarse de forma consistente a toda la API.

## Comandos principales

| Comando | Uso |
|---|---|
| `uv run ruff check .` | Ejecuta el linter sobre toda la API |
| `uv run ruff check . --fix` | Aplica las correcciones seguras disponibles y vuelve a comprobar |
| `uv run ruff format .` | Formatea el código |
| `uv run ruff format --check .` | Comprueba el formato sin modificar archivos |
| `uv run ruff rule <codigo>` | Explica una regla concreta |
| `uv run ruff config [opcion]` | Lista o explica opciones de configuración |
| `uv run ruff analyze graph .` | Genera el mapa de dependencias entre módulos Python |
| `uv run ruff clean` | Elimina las cachés de Ruff desde el directorio actual |
| `uv run ruff version` | Muestra la versión instalada |
| `uv run ruff help [comando]` | Muestra la ayuda general o de un comando |

## Flujo durante el desarrollo

Ejecuta primero las correcciones del linter y después el formatter:

```bash
uv run ruff check . --fix
uv run ruff format .
```

`ruff check --fix` corrige infracciones para las que existe una corrección segura. `ruff format` normaliza exclusivamente el formato. Un comando no sustituye al otro.

Ruff no aplica correcciones inseguras con este flujo. Revisa cada caso antes de usar `--unsafe-fixes`, porque esas modificaciones pueden alterar el comportamiento del programa.

## Verificación antes de integrar

Antes de hacer commit, y como controles equivalentes para CI, ejecuta comandos que no modifiquen archivos:

```bash
uv run ruff check .
uv run ruff format --check .
```

Ambos comandos deben terminar correctamente. El primero falla cuando encuentra infracciones de linting; el segundo falla cuando algún archivo requiere formateo.

## Revisar una ruta concreta

Las rutas son relativas a `api/`. Puedes limitar la revisión durante el desarrollo:

```bash
uv run ruff check app/main.py
uv run ruff check app/
uv run ruff format app/
```

La verificación final debe conservar `.` como objetivo para no omitir código, migraciones o pruebas.

## Entender un diagnóstico

Cada diagnóstico incluye un código, por ejemplo:

```text
F401 imported but unused
```

Consulta la explicación de esa regla con:

```bash
uv run ruff rule F401
```

Para mostrar la documentación de todas las reglas disponibles:

```bash
uv run ruff rule --all
```

Para consultar todas las opciones de configuración o una opción concreta:

```bash
uv run ruff config
uv run ruff config line-length
```

## Errores comunes

- Ejecutar solo `ruff check --fix`: las correcciones del linter no garantizan que el código tenga el formato esperado.
- Ejecutar solo `ruff format`: el formatter no detecta imports sin usar, errores de reglas asíncronas ni otras infracciones del linter.
- Ejecutar desde la raíz del monorepo como si Ruff estuviera configurado para todos los módulos: la dependencia y el perfil actuales pertenecen a la API.
- Verificar solamente el archivo modificado antes de integrar: la configuración o un autofix puede afectar la coherencia del proyecto completo.
- Activar correcciones inseguras sin revisar el diff: una corrección técnicamente válida puede cambiar la intención del código.

## Lista de verificación

- [ ] Los comandos se ejecutaron desde `api/`.
- [ ] `uv run ruff check .` terminó sin infracciones.
- [ ] `uv run ruff format --check .` confirmó el formato.
- [ ] Las correcciones automáticas fueron revisadas en el diff.
- [ ] Cualquier cambio de configuración representa una regla compartida por toda la API.
