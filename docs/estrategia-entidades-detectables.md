# Estrategia para entidades detectables

## Problema

La capa intermedia usa dos fuentes principales para detectar informacion sensible:

1. Modelos de reconocimiento de entidades nombradas.
2. Reglas controladas mediante expresiones regulares, validadores y diccionarios.

Estas fuentes no tienen el mismo nivel de control.

La deteccion basada en modelos depende de la taxonomia con la que cada modelo fue entrenado. Por esta razon, no se debe asumir que todos los modelos detectaran las mismas categorias ni con el mismo nombre. Un modelo puede detectar `PERSON`, otro `NOMBRE`, otro `PATIENT`, y otro puede no detectar nombres generales si fue entrenado para un dominio clinico.

En cambio, la deteccion por reglas si es modificable directamente dentro del proyecto. Esto permite agregar entidades locales como cedula ecuatoriana, RUC, telefonos nacionales, correos institucionales y otros patrones propios del contexto universitario ecuatoriano.

## Decision de diseno

La tesis no debe prometer una lista unica y fija de entidades detectadas por todos los modelos.

En su lugar, se usara una estrategia de tres niveles:

1. Catalogo objetivo de la tesis.
2. Etiquetas observadas por cada modelo probado.
3. Entidades controladas por reglas propias.

## 1. Catalogo objetivo de la tesis

El catalogo objetivo representa las entidades que la investigacion considera relevantes para medir exposicion de informacion sensible.

Este catalogo no depende de un modelo especifico. Sirve como referencia para:

- Definir la taxonomia.
- Anotar escenarios experimentales.
- Calcular el indice de exposicion.
- Comparar resultados entre modelos.
- Identificar brechas de deteccion.

Ejemplos:

| Entidad objetivo | Descripcion | Fuente esperada |
| --- | --- | --- |
| PERSONA | Nombre o apellido de una persona | Modelo |
| UBICACION | Ciudad, direccion o lugar | Modelo o reglas |
| INSTITUCION | Universidad, facultad, empresa o dependencia | Modelo o diccionario |
| CORREO | Correo personal o institucional | Reglas |
| TELEFONO | Numero celular o convencional | Reglas |
| CEDULA_EC | Cedula ecuatoriana | Reglas + validador |
| RUC_EC | Registro unico de contribuyentes | Reglas + validador |
| DATO_ACADEMICO | Nota, matricula, carrera, horario, materia | Diccionario + contexto |
| DATO_FINANCIERO | Beca, deuda, pago, cuenta bancaria | Reglas + contexto |
| SALUD | Diagnostico, certificado medico, condicion de salud | Modelo + contexto |
| RUTINA | Horarios, ubicaciones frecuentes, habitos | Contexto |

## 2. Etiquetas observadas por modelo

Cada modelo probado debe tener un registro propio de etiquetas detectables.

Ejemplo de registro:

```text
modelo: OpenMed/OpenMed-PII-Spanish-QwenMed-XLarge-600M-v1
tipo: clasificacion de tokens
idioma: espanol
etiquetas_observadas:
  - por extraer desde la configuracion del modelo
  - por confirmar con pruebas empiricas
```

La forma tecnica recomendada para obtener etiquetas es leer la configuracion del modelo:

```python
modelo.config.id2label
```

Esto permite saber que etiquetas conoce el modelo sin asumirlas manualmente.

## 3. Entidades controladas por reglas propias

Estas entidades si son responsabilidad directa del proyecto.

Inicialmente deben incluir:

| Entidad | Metodo |
| --- | --- |
| CEDULA_EC | Expresion regular + validacion de digito verificador |
| RUC_EC | Expresion regular + validacion |
| CORREO | Expresion regular |
| CORREO_INSTITUCIONAL | Expresion regular + dominios institucionales |
| TELEFONO_EC | Expresion regular |
| USUARIO_INSTITUCIONAL | Expresion regular o diccionario |
| CODIGO_ACADEMICO | Expresion regular o diccionario |

Estas entidades permiten adaptar la capa intermedia al contexto ecuatoriano sin modificar ni reentrenar el modelo.

## Normalizacion de etiquetas

Como cada modelo puede devolver etiquetas diferentes, se debe crear una capa de normalizacion.

Ejemplo:

| Etiqueta del modelo | Entidad normalizada |
| --- | --- |
| PERSON | PERSONA |
| PER | PERSONA |
| NAME | PERSONA |
| LOCATION | UBICACION |
| LOC | UBICACION |
| ORGANIZATION | INSTITUCION |
| ORG | INSTITUCION |
| EMAIL | CORREO |
| PHONE | TELEFONO |

Esta normalizacion permite comparar modelos aunque sus etiquetas internas sean distintas.

## Sobre ajuste fino de modelos

El ajuste fino permitiria entrenar o adaptar un modelo para detectar un conjunto especifico de entidades. Sin embargo, implica:

- Preparar un conjunto de datos anotado.
- Definir una taxonomia de etiquetas estable.
- Reentrenar o ajustar la cabeza de clasificacion del modelo.
- Evaluar perdida de rendimiento en etiquetas anteriores.
- Aumentar el alcance tecnico de la tesis.

Por ahora, el ajuste fino queda fuera del alcance inicial. La estrategia recomendada es:

1. Usar modelos existentes como detectores candidatos.
2. Extraer sus etiquetas reales.
3. Normalizar sus salidas a una taxonomia comun.
4. Complementar sus limitaciones con reglas locales.
5. Evaluar empiricamente cual combinacion reduce mejor la exposicion.

## Implicacion para la tesis

La tesis debe formular la deteccion asi:

> La capa intermedia integra modelos de reconocimiento de entidades nombradas como detectores variables y reglas locales como detectores controlados. Las salidas de los modelos se normalizan hacia una taxonomia comun de la investigacion, mientras que las entidades ecuatorianas y academicas criticas se implementan mediante reglas y validadores propios.

Esta formulacion evita depender de una unica taxonomia de modelo y permite comparar varios modelos sin cambiar el objetivo de investigacion.

## Evaluacion recomendada

Cada modelo candidato debe evaluarse con los mismos escenarios anotados.

Para cada modelo se debe registrar:

- Etiquetas que declara en su configuracion.
- Entidades que detecta realmente en los escenarios.
- Falsos positivos.
- Falsos negativos.
- Entidades que solo detecta la capa de reglas.
- Entidades que requieren decision contextual.
- Tiempo de procesamiento.

## Resultado esperado

La capa intermedia no queda atada a un modelo especifico. El sistema puede probar varios modelos y comparar sus resultados sin cambiar la taxonomia de tesis ni las reglas locales.
