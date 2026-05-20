# Lista de trabajo tecnico inicial

## Proposito

Esta lista de trabajo ordena el trabajo tecnico necesario para pasar del cuaderno actual a una capa intermedia evaluable.

## Estado actual

El prototipo actual en `anonimizador-contextual-datos-sensibles.ipynb` incluye:

- Preprocesamiento basico.
- Deteccion por expresiones regulares.
- Uso de un modelo de reconocimiento de entidades nombradas en espanol.
- Fusion simple entre expresiones regulares y reconocimiento de entidades nombradas.
- Reemplazo de entidades por etiquetas genericas.

Todavia no incluye:

- Decision contextual real.
- Validacion de cedula ecuatoriana.
- Taxonomia formal.
- Evaluacion tecnica.
- Conjunto de datos anotado.
- Estructura de codigo en `src`.

## Lista de trabajo priorizado

| ID | Prioridad | Tarea | Resultado esperado |
| --- | --- | --- | --- |
| T01 | Alta | Crear estructura base en `src` | Modulos separados para deteccion, decision y transformacion |
| T02 | Alta | Renombrar `SSN` a `EC_CEDULA` | Etiquetas alineadas al contexto ecuatoriano |
| T03 | Alta | Implementar validador de cedula ecuatoriana | Menos falsos positivos |
| T04 | Alta | Evitar problemas de posiciones | Reemplazos correctos sobre texto original |
| T05 | Alta | Implementar taxonomia en codigo | Sensibilidad por tipo de entidad |
| T06 | Alta | Implementar `es_dato_sensible(entidad, contexto)` | Decision contextual inicial |
| T07 | Alta | Implementar etiquetas semanticas consistentes | `<PERSONA_1>`, `<CEDULA_1>`, etc. |
| T08 | Media | Agregar deteccion de RUC | Mayor cobertura local |
| T09 | Media | Agregar diccionario academico | Mejor deteccion contextual |
| T10 | Media | Crear conjunto de datos anotado en JSON/CSV | Evaluacion automatica |
| T11 | Media | Crear archivo de evaluacion | Precision, exhaustividad, F1 |
| T12 | Media | Calcular indice de exposicion | Metrica principal de tesis |
| T13 | Media | Extraer etiquetas declaradas por cada modelo | Conocer que entidades puede devolver cada modelo |
| T14 | Media | Crear normalizador de etiquetas por modelo | Comparar modelos bajo una taxonomia comun |
| T15 | Media | Registrar resultados por modelo candidato | Evaluar alternativas sin cambiar la arquitectura |
| T16 | Baja | Crear interfaz grafica simple | Util para piloto con usuarios |
| T17 | Baja | Exportar registros experimentales | Analisis posterior |

## Estructura sugerida de codigo

```text
src/
  anonimizador_contextual/
    __init__.py
    patrones.py
    validadores.py
    reconocimiento_entidades.py
    normalizacion_etiquetas.py
    fusion.py
    taxonomia.py
    decision_contextual.py
    transformacion.py
    flujo.py
    evaluacion.py
```

## Primer incremento tecnico recomendado

Para Iteracion 1 o Iteracion 2, el primer incremento de codigo deberia lograr:

1. Recibir texto.
2. Detectar correo electronico, telefono y cedula.
3. Validar cedula.
4. Transformar con etiquetas semanticas.
5. Devolver entidades detectadas con tipo, posicion, sensibilidad y razon.

## Criterio de terminado del producto minimo viable

El producto minimo viable tecnico estara listo cuando este caso funcione:

Entrada:

```text
Me llamo Esteban Molina, mi cedula es 1711122233 y mi correo es esteban@gmail.com.
```

Salida:

```text
Me llamo <PERSONA_1>, mi cedula es <CEDULA_1> y mi correo es <CORREO_1>.
```

Ademas, debe devolver una lista de entidades:

```json
[
  {
    "texto": "Esteban Molina",
    "tipo": "PERSONA",
    "sensibilidad": "alta",
    "accion": "transformar",
    "razon": "Nombre de persona"
  }
]
```

## Riesgos tecnicos inmediatos

| Riesgo | Causa | Mitigacion |
| --- | --- | --- |
| El modelo de reconocimiento de entidades nombradas no detecta nombres locales | Modelo no adaptado al dominio | Complementar con reglas y pruebas |
| Las expresiones regulares detectan numeros que no son cedulas | Patron demasiado general | Usar validador |
| Transformacion rompe texto | Posiciones incorrectos | Reemplazar en orden descendente y conservar texto original |
| Se marcan demasiadas entidades | Reglas muy agresivas | Ajustar decision contextual |
| Se omiten entidades sensibles | Taxonomia incompleta | Ampliar escenarios anotados |





