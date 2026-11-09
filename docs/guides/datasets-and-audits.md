# Conjuntos de datos y auditorías

**Objetivo.** Esta guía define cómo entra un conjunto de datos al repositorio, dónde viven sus archivos, cómo se audita y cómo se entrega la evidencia para revisión. Aplica la misma organización a cada conjunto de datos nuevo; adapta las comprobaciones a los datos, no a la estructura.

**Lector previsto.** Cualquier persona que agregue un conjunto de datos, prepare datos o revise una auditoría antes de que el proyecto pase a entrenamiento.

## Principios

1. **Un conjunto de datos es una unidad.** El contenido, el código de preparación, el notebook de auditoría, las figuras y el informe se atribuyen a un único conjunto de datos. Nada que pertenezca a un conjunto de datos vive en una carpeta compartida y ambigua.
2. **Git versiona el significado, DVC versiona los bytes.** Los contenidos grandes se guardan fuera de Git; Git conserva los metadatos que identifican la versión exacta.
3. **Una auditoría es de solo lectura.** Las auditorías miden y documentan. Nunca reparan, deduplican ni reescriben la versión congelada. Las correcciones pertenecen a una versión posterior del conjunto de datos.
4. **La evidencia debe ser reproducible.** Cada número de un informe lo produce un artefacto ejecutable guardado junto a él, no se copia a mano desde una sesión interactiva.
5. **Un notebook debe explicarse solo.** Quien revisa abre el notebook (o su PDF) sin conversación previa y entiende qué se midió, por qué importa y qué sigue.
6. **Solo se versionan los artefactos útiles.** Se versionan el código de transformación, los notebooks con sus salidas, los informes, las figuras y la ficha del conjunto de datos. No se versionan los contenidos, los entornos, las cachés ni los PDF generados.

## Estructura del espacio de trabajo

La estructura es estable entre conjuntos de datos. Reemplaza `<dataset>` por el nombre del conjunto.

```
ml/
├── data/
│   ├── raw/<payload>              # Contenido gestionado por DVC (no versionado en Git)
│   └── processed/<payload>        # Contenido derivado (no versionado en Git)
├── src/pii_ml/data/
│   ├── audit.py                   # Estadísticas y detección reutilizables
│   └── validation.py              # Comprobaciones estructurales y de anotación reutilizables
├── datasets/
│   └── <dataset>/
│       ├── README.md              # Ficha del conjunto de datos
│       ├── notebooks/
│       │   └── NNN_<purpose>.ipynb
│       └── reports/
│           ├── <purpose>_v<N>.md
│           └── figures/
│               └── NNN_<name>.png
├── scripts/
│   └── render_report_pdf.py       # Informe Markdown a PDF
├── pyproject.toml                 # Entorno y herramientas
├── uv.lock
└── .gitignore
```

`data/` contiene los archivos gestionados por DVC. `src/pii_ml/` contiene el código realmente reutilizable entre conjuntos de datos. `datasets/<dataset>/` contiene todo lo que describe o analiza un conjunto de datos. Una comprobación usada por un solo conjunto de datos permanece dentro de su carpeta hasta que un segundo la necesite; entonces se mueve a `src/pii_ml/` con sus pruebas.

La visión general del espacio de trabajo está en [`ml/README.md`](../../ml/README.md).

## Requisitos

| Herramienta | Uso |
|---|---|
| `uv` | Crea el entorno y ejecuta código desde `ml/` |
| `dvc` | Versiona y transfiere los contenidos del conjunto de datos |
| Navegador Chromium (Chrome o Edge) | Renderiza informes a PDF sin LaTeX |

```powershell
cd ml
uv sync
dvc version
```

Todos los comandos del conjunto de datos se ejecutan desde `ml/`, la raíz de DVC de este espacio de trabajo.

## 1. Registrar o localizar el conjunto de datos

Si el contenido ya existe y está versionado, pasa directamente a restaurarlo. Para agregar contenido nuevo:

```powershell
cd ml
dvc add data/raw/<file-or-directory>
git add data/raw/<file-or-directory>.dvc data/raw/.gitignore
```

`dvc add` escribe `<name>.dvc` con el hash del contenido, el tamaño y la cantidad de archivos, y DVC agrega la ruta del contenido a `data/raw/.gitignore`. Haz commit del archivo `.dvc`; nunca hagas commit del contenido. Los metadatos `.dvc` son la identidad de la versión del conjunto de datos, así que una auditoría posterior siempre indica qué hash leyó.

## 2. Configurar el remoto por máquina

Un remoto le dice a DVC dónde viven los bytes. La URL del remoto puede contener credenciales o rutas propias de la máquina, así que debe quedar fuera de Git:

```powershell
cd ml
dvc remote add --local -d <remote-name> <remote-url>
dvc remote list --local
```

- `--local` escribe `.dvc/config.local`, que DVC mantiene sin versionar. Haz commit de `.dvc/config` solo cuando la configuración del remoto sea realmente compartible y no contenga credenciales.
- Las formas admitidas incluyen un directorio local o montado (`D:\dvc-storage`, una carpeta de Drive sincronizada) y un backend nativo como `gdrive://<folder-id>`. Los backends nativos necesitan su propia autenticación y pueden requerir dependencias adicionales.
- Nunca pongas tokens, JSON de cuentas de servicio ni rutas personales del sistema de archivos en documentación, commits o notebooks.

Antes de continuar, comprueba que `git status` no liste la configuración del remoto ni ningún archivo de credenciales.

## 3. Restaurar y verificar el contenido

```powershell
cd ml
dvc pull data/raw/<file-or-directory>.dvc
dvc status data/raw/<file-or-directory>.dvc
```

`dvc status` debe informar que los datos están al día. Después concilia la copia de trabajo con los metadatos: la cantidad de archivos y el tamaño total deben coincidir con los números del archivo `.dvc`. Un desajuste significa que la copia de trabajo no es la versión congelada; no ejecutes la auditoría hasta que coincida.

## 4. Escribir la ficha del conjunto de datos

Crea `datasets/<dataset>/README.md` antes de analizar. Es el punto de entrada que sobrevive a la auditoría:

- Identidad del conjunto de datos: versión de DVC (hash), cantidad de archivos y tamaño total.
- Qué contiene el conjunto de datos y qué formatos usa.
- Tabla de contenidos: una fila por artefacto con su propósito.
- Comando de restauración.
- Cómo reproducir la auditoría.
- Características conocidas y problemas abiertos.
- Enlaces al notebook y al informe.

La ficha enuncia hechos estables. Las mediciones detalladas pertenecen al informe, no a la ficha.

## 5. Inspeccionar antes de escribir código

Lee primero una muestra de cada artefacto. Identifica:

- Archivos, formatos, tamaños y codificaciones.
- Esquema de los registros: campos, tipos, identificadores y cómo se relacionan los artefactos.
- Estructura de particiones y vocabulario de etiquetas.
- Qué declara el conjunto de datos sobre sí mismo que pueda verificarse de forma independiente.

A partir de esa inspección, decide qué preguntas de auditoría aplican. El conjunto de preguntas por defecto está abajo; conserva lo que el conjunto de datos soporte, elimina lo que no y agrega comprobaciones específicas del dominio cuando los datos tengan un contrato que valga la pena verificar.

| Pregunta | Evidencia típica |
|---|---|
| ¿Qué contiene el conjunto de datos? | Inventario de archivos, tamaños, conteos de registros |
| ¿Cuál es el contrato de los registros? | Presencia de campos, tipos, uniones |
| ¿Los datos son estructuralmente válidos? | Campos faltantes, duplicados, coincidencia de longitudes, gramática |
| ¿Qué etiquetas existen? | Clases declaradas frente a observadas |
| ¿Cómo se distribuyen los datos? | Frecuencia de clases, tipos de documento, longitudes, desbalance |
| ¿Hay duplicados? | Exactos, normalizados y candidatos casi duplicados |
| ¿Las particiones están aisladas y son comparables? | Solapamiento de identificadores y texto, presencia de clases |
| ¿Las anotaciones son correctas? | Validez de límites, correspondencia con los valores declarados |
| ¿Qué cobertura existe? | Clases raras y ausentes por partición |
| ¿El conjunto de datos está listo para la siguiente fase? | Veredicto con condiciones explícitas |

## 6. Extender los módulos reutilizables solo cuando se justifique

`pii_ml.data.audit` devuelve datos simples: inventario, esquema, conteos, longitudes, duplicados, particiones, reutilización y correspondencia. `pii_ml.data.validation` devuelve problemas agregados con severidad, código y muestras.

Reglas:

- Devuelve datos, no texto formateado. Los notebooks y los informes formatean los resultados.
- Agrega los hallazgos; nunca imprimas una línea por registro defectuoso.
- Mantén cada función independiente de una ruta concreta del conjunto de datos; pasa las rutas como argumentos.
- Agrega una función a `src/pii_ml/` solo cuando sea agnóstica al conjunto de datos. Si no, mantenla en el notebook o en un script local del conjunto.
- Ejecuta el linter después de los cambios:

```powershell
cd ml
uv run ruff check src
uv run ruff format --check src
```

## 7. Escribir el notebook de auditoría

Ubícalo en `datasets/<dataset>/notebooks/NNN_<purpose>.ipynb`. Quien revisa debe poder leerlo como un documento autónomo.

Contenido obligatorio:

1. **Título y propósito** — qué responde la auditoría y qué decisiones sostiene.
2. **Audiencia** — quién la revisa y qué necesita para aprobar la siguiente fase.
3. **Identidad del conjunto de datos** — hash de DVC, cantidad de archivos, tamaño y la fecha o el commit de la ejecución cuando sea relevante.
4. **Cómo ejecutarlo** — entorno, comando y kernel, dentro del notebook.
5. **Definiciones** — cada término del dominio que el lector necesite (registro, etiqueta, partición, cobertura, duplicado).
6. **Alcance y método** — qué se mide, qué se evita a propósito y por qué.
7. **Una sección por pregunta** — cada una responde qué se mide, por qué importa y cómo leer el resultado.
8. **Conclusiones y limitaciones** — qué sostiene la evidencia y qué no puede probar.
9. **Siguientes pasos** — decisiones concretas que debe tomar la siguiente fase.

Reglas:

- Solo lectura: nunca escribas dentro de `data/`.
- Calcula rutas relativas al espacio de trabajo; nunca fijes una ruta de máquina.
- Guarda las figuras con nombres deterministas en `reports/figures/`; cada figura debe tener título y ejes etiquetados.
- Mantén la interpretación coherente con los valores calculados. Si cambia un umbral, actualiza el texto que lo cita.
- No dependas de narración externa, historial de chat ni un documento de explicación aparte.
- Versiona el notebook **con sus salidas** para que la evidencia sea visible sin volver a ejecutarlo.

## 8. Ejecutar y almacenar la evidencia

```powershell
cd ml
uv run jupyter nbconvert --to notebook --execute --inplace `
  datasets/<dataset>/notebooks/<notebook>.ipynb
```

Haz commit del notebook ejecutado y de las figuras generadas. Si la ejecución falla, corrige el código o el entorno; no hagas commit de un notebook con salidas de error.

## 9. Escribir el informe

Ubícalo en `datasets/<dataset>/reports/<purpose>_v<N>.md`. El informe es el artefacto de decisión revisable; el notebook es su evidencia.

Estructura obligatoria:

1. **Tabla de cabecera** — estado, versión del conjunto de datos, archivos y tamaño, conteos de registros, enlaces a la evidencia.
2. **Veredicto** — listo o no, con condiciones explícitas.
3. **Método y reproducibilidad** — módulos, comandos, tiempo de ejecución y qué fue de solo lectura.
4. **Hallazgos por pregunta** — tablas y las figuras que los sostienen.
5. **Limitaciones** — qué no pueden detectar las comprobaciones.
6. **Recomendaciones** — decisiones que debe tomar la siguiente fase, en orden de prioridad.
7. **Condición de avance** — qué debe ser cierto antes de que el conjunto de datos avance.

Reglas:

- Cada número debe ser rastreable hasta una celda del notebook.
- Separa los hechos medidos de la interpretación; no afirmes garantías que las comprobaciones no pueden sostener.
- Indica la versión del conjunto de datos a la que se refiere el informe. Una versión nueva necesita un informe nuevo.
- Escribe el informe en inglés con secciones y etiquetas de tabla consistentes.

## 10. Renderizar el PDF para revisión

El PDF es un artefacto generado y no se versiona. Incorpora las figuras para que quien revisa pueda leer un solo archivo.

```powershell
cd ml
uv run python scripts/render_report_pdf.py datasets/<dataset>/reports/<report>.md
```

El script convierte Markdown a HTML A4 con estilos, incorpora las imágenes relativas y lo imprime con Chrome o Edge en modo headless. Usa `--browser <path>` cuando el navegador no esté en una ubicación estándar, y `--output <path>` para cambiar el destino. Mantén el informe Markdown como fuente de verdad; nunca edites el PDF.

## Reglas de versionado

| Se versiona | Se ignora |
|---|---|
| Metadatos `.dvc` | Contenidos del conjunto de datos bajo `data/` |
| Ficha del conjunto de datos | `.venv/`, `__pycache__/`, `*.egg-info/` |
| Notebook con salidas | `.ipynb_checkpoints/` |
| Informe Markdown y figuras | PDF y HTML generados del informe |
| Código reutilizable de auditoría y validación | Configuración local de DVC y credenciales |
| `pyproject.toml` y `uv.lock` | Rutas propias de la máquina |

El `.gitignore` del espacio de trabajo ya cubre entornos, cachés, checkpoints de notebooks e informes generados. Extiéndelo solo para tipos de artefacto nuevos y prefiere patrones estrechos sobre los globales.

## Convenciones de nombres

| Artefacto | Patrón | Ejemplo |
|---|---|---|
| Carpeta del conjunto de datos | `datasets/<dataset>/` | `datasets/<dataset>/` |
| Notebook | `NNN_<purpose>.ipynb` | `001_dataset_audit.ipynb` |
| Informe | `<purpose>_v<N>.md` | `dataset_audit_v1.md` |
| Figura | `NNN_<name>.png` | `001_document_types.png` |
| Script local del conjunto de datos | `scripts/<verb>_<object>.py` | `scripts/convert_csv_to_jsonl.py` |

Usa nombres de carpeta en minúsculas y sin guiones que coincidan con el nombre del artefacto de DVC, para que metadatos, contenido y artefactos sean fáciles de correlacionar.

## Lista de verificación para la entrega

- [ ] Contenido restaurado y `dvc status` limpio.
- [ ] La copia de trabajo coincide con la cantidad de archivos y el tamaño de los metadatos.
- [ ] Ficha del conjunto de datos escrita con identidad, contenidos y pasos de reproducción.
- [ ] Comprobaciones reutilizables extendidas solo donde generalizan; el linter pasa.
- [ ] El notebook es autónomo, de solo lectura y ejecutado con las salidas versionadas.
- [ ] Figuras guardadas en `reports/figures/` con nombres deterministas.
- [ ] El informe indica la versión del conjunto de datos, el veredicto, las condiciones y las limitaciones.
- [ ] PDF renderizado para revisión y dejado sin versionar.
- [ ] `git status` no muestra contenido, credenciales, entornos ni PDF generados.
- [ ] Navegación actualizada en esta área de guías si se introdujo una convención nueva.

## Diagnóstico

| Síntoma | Causa | Acción |
|---|---|---|
| `no remote` al hacer pull | El remoto está configurado solo en otra máquina | Configúralo localmente con `--local` |
| El pull funciona pero los archivos no coinciden con los metadatos | La copia de trabajo pertenece a otra versión | Vuelve a hacer pull del archivo `.dvc` específico; no lo agregues de nuevo a ciegas |
| El notebook no puede importar `pii_ml` | El notebook se ejecuta fuera del entorno `ml` | Selecciona el kernel del entorno `ml` después de `uv sync` |
| No se crea el PDF | No se encontró un navegador Chromium | Pasa `--browser` de forma explícita |
| Mojibake en la salida de la terminal | Codificación de la consola, no del contenido del archivo | Lee los archivos con UTF-8 explícito; verifícalo con Python |
| Archivos enormes bloquean el editor | Se abrió el contenido directamente | Procesa JSONL en streaming e inspecciona muestras |
| Los números del informe no coinciden con el notebook | Se copió el texto en lugar de recalcularlo | Vuelve a ejecutar el notebook y actualiza el informe |

## Evolucionar este proceso

- Un tipo nuevo de conjunto de datos (tabular, audio, imágenes) puede necesitar funciones nuevas de inventario y validación. Agrégalas a `src/pii_ml/` solo cuando generalicen y mantén los supuestos específicos en la carpeta del conjunto.
- Una pregunta nueva pertenece a la auditoría solo si cambia una decisión. Documenta en el notebook por qué se agregó.
- Cuando cambie la estructura misma, actualiza esta guía y el `README.md` del espacio de trabajo en el mismo cambio, para que el siguiente conjunto de datos parta de una descripción correcta.
