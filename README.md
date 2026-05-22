# Contextual PII Anonymizer

Prototipo de capa intermedia contextual para desidentificar informacion sensible en consultas academicas en espanol, con foco en el contexto universitario ecuatoriano.

## Estructura actual

- `src/contextual_pii_anonymizer/cli.py`: punto de entrada de linea de comandos.
- `src/contextual_pii_anonymizer/__main__.py`: permite ejecutar el paquete con `python -m contextual_pii_anonymizer`.
- `src/contextual_pii_anonymizer/core/`: estructuras compartidas.
- `src/contextual_pii_anonymizer/detection/`: reglas, adaptador de modelo NER y validadores ecuatorianos.
- `src/contextual_pii_anonymizer/context/`: taxonomia y decision contextual de sensibilidad.
- `src/contextual_pii_anonymizer/anonymization/`: transformacion semantica.
- `src/contextual_pii_anonymizer/processing/`: fusion y pipeline principal.
- `src/contextual_pii_anonymizer/evaluation/`: metricas sobre escenarios anotados.
- `data/escenarios_iniciales.json`: escenarios anotados iniciales derivados de la documentacion.
- `scripts/evaluar_escenarios.py`: evaluador inicial de precision, exhaustividad, F1 e indice de exposicion.
- `tests/test_pipeline.py`: pruebas unitarias sin dependencias externas.
- `docs/`: definiciones de alcance, arquitectura, taxonomia y escenarios.

## Uso esperado

Instalar el proyecto en modo editable dentro del entorno virtual:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Ejecutar pruebas:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Procesar texto desde la linea de comandos:

```powershell
.\.venv\Scripts\python.exe -m contextual_pii_anonymizer anonymize "Me llamo Esteban Molina, mi cedula es 1711122232 y mi correo es esteban@gmail.com."
```

Evaluar escenarios anotados:

```powershell
.\.venv\Scripts\python.exe -m contextual_pii_anonymizer evaluate data\escenarios_iniciales.json
```

Para procesar texto desde codigo:

```python
from contextual_pii_anonymizer import process_text

resultado = process_text(
    "Me llamo Esteban Molina, mi cedula es 1711122232 y mi correo es esteban@gmail.com."
)
print(resultado["salida"])
```

Salida esperada:

```text
Me llamo <PERSONA_1>, mi cedula es <CEDULA_EC_1> y mi correo es <CORREO_1>.
```

## Pendientes marcados en codigo

Los puntos que requieren investigacion, validacion con tutor o ajuste posterior estan marcados con:

```python
# TODO: pending research
```
