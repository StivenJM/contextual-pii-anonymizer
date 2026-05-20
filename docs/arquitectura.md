# Arquitectura de la capa intermedia contextual de desidentificacion

## Proposito

La capa intermedia actua entre el usuario y un modelo de lenguaje grande. Su objetivo es detectar informacion sensible en consultas academicas, decidir su nivel de sensibilidad segun el contexto y transformar los datos antes de enviarlos al modelo.

La arquitectura busca equilibrar dos necesidades:

- Reducir la exposicion de informacion sensible.
- Conservar suficiente significado para que el modelo de lenguaje grande pueda responder de forma util.

## Vista general

```text
Usuario
  |
  v
[1. Entrada y normalizacion]
  |
  v
[2. Deteccion hibrida]
  |
  v
[3. Fusion y resolucion de entidades]
  |
  v
[4. Decision contextual de sensibilidad]
  |
  v
[5. Transformacion semantica]
  |
  v
[6. Registro experimental]
  |
  v
modelo de lenguaje grande
```

## 1. Entrada y normalizacion

Esta capa recibe el texto original del usuario y genera representaciones auxiliares para analisis.

Responsabilidades:

- Conservar la consulta original.
- Aplicar limpieza minima.
- Crear una version auxiliar normalizada cuando sea necesario.
- Evitar perder posiciones de caracteres para no reemplazar texto incorrecto.

Regla tecnica importante:

> Las transformaciones finales deben aplicarse sobre el texto original, no sobre una version que haya cambiado longitudes o posiciones.

## 2. Deteccion hibrida

Esta capa combina varios mecanismos de deteccion.

La deteccion basada en modelos se considera variable, porque cada modelo puede estar entrenado con una taxonomia diferente de entidades. Por ello, la arquitectura no depende de que todos los modelos detecten las mismas categorias. Las salidas de cada modelo deben normalizarse hacia la taxonomia comun de la tesis.

### 2.1 Motor de patrones

Detecta datos estructurados mediante reglas, expresiones regulares y validadores.

Entidades iniciales:

- Cedula ecuatoriana.
- RUC.
- Correo electronico.
- Telefono celular o convencional.
- Fechas.
- Codigos academicos o institucionales.

### 2.2 Motor de reconocimiento de entidades nombradas

Detecta entidades no estructuradas que dependen del contexto.

El modelo actual usado como punto de partida es:

```text
OpenMed/OpenMed-PII-Spanish-QwenMed-XLarge-600M-v1
```

Sin embargo, la arquitectura permite probar otros modelos. Para cada modelo se debe registrar su conjunto real de etiquetas y mapearlas hacia entidades normalizadas del proyecto.

Entidades iniciales:

- Personas.
- Instituciones.
- Lugares.
- Organizaciones.
- Cargos.

### 2.3 Diccionarios contextuales

Refuerzan el reconocimiento del dominio universitario y ecuatoriano.

Ejemplos:

- Matricula.
- Carrera.
- Facultad.
- Docente.
- Nota.
- Beca.
- Campus.
- Secretaria.
- Departamento.

### 2.4 Normalizacion de etiquetas

Convierte las etiquetas especificas de cada modelo en categorias comunes del proyecto.

Ejemplo:

| Etiqueta del modelo | Categoria normalizada |
| --- | --- |
| PERSON | PERSONA |
| PER | PERSONA |
| NAME | PERSONA |
| LOCATION | UBICACION |
| LOC | UBICACION |
| ORGANIZATION | INSTITUCION |
| ORG | INSTITUCION |

Esta capa permite comparar varios modelos aunque cada uno use nombres o categorias distintas.

## 3. Fusion y resolucion de entidades

Esta capa une los hallazgos de expresiones regulares, reconocimiento de entidades nombradas y diccionarios.

Reglas iniciales:

1. Priorizar entidades estructuradas validadas sobre entidades detectadas por reconocimiento de entidades nombradas.
2. Conservar la entidad mas larga cuando dos detecciones representan el mismo dato.
3. Registrar todas las fuentes que detectaron una entidad.
4. Resolver solapamientos antes de transformar el texto.
5. Mantener trazabilidad de cada decision.

## 4. Decision contextual de sensibilidad

Esta es la capa central del aporte de tesis. No basta con detectar entidades; la capa intermedia debe decidir si una entidad representa riesgo segun su contexto.

Ejemplos de decision:

| Caso | Decision sugerida |
| --- | --- |
| Nombre + cedula | Sensibilidad alta |
| Nombre + direccion | Sensibilidad alta |
| Nombre + salud | Sensibilidad critica |
| Nombre + dato financiero | Sensibilidad critica |
| Correo personal | Sensibilidad alta |
| Correo institucional aislado | Sensibilidad media |
| Telefono institucional publico | Sensibilidad baja o media |
| Dato academico asociado a una persona | Sensibilidad alta |

Cada entidad debe incluir:

- Tipo.
- Nivel de sensibilidad.
- Decision.
- Razon.
- Accion recomendada.

## 5. Transformacion semantica

Esta capa reemplaza los datos sensibles con representaciones que preservan el significado.

Estrategia recomendada para la tesis:

```text
Me llamo <PERSONA_1>, mi cedula es <CEDULA_1> y estudio en <INSTITUCION_1>.
```

Acciones posibles:

- Etiqueta semantica.
- Pseudonimizacion.
- Enmascaramiento parcial.
- Advertencia al usuario.
- Bloqueo del envio en casos criticos.

Para el producto minimo viable se recomienda priorizar etiquetas semanticas consistentes.

## 6. Registro experimental

Esta capa guarda evidencia anonima para evaluar la capa intermedia.

Campos recomendados:

- ID anonimo del participante.
- Perfil: tecnico o no tecnico.
- Condicion: con capa intermedia o sin capa intermedia.
- Escenario experimental.
- Entidades esperadas.
- Entidades detectadas.
- Entidades omitidas.
- Entidades transformadas.
- Indice de exposicion.
- Tiempo de interaccion.
- Aceptacion o rechazo de sugerencias.

## Version minima viable

La primera version defendible debe incluir:

1. Deteccion de correo, telefono, cedula y nombres.
2. Validacion de cedula ecuatoriana.
3. Fusion basica de entidades.
4. Decision contextual simple.
5. Transformacion con etiquetas semanticas.
6. Registro de entidades detectadas y transformadas.
7. Evaluacion con escenarios anotados.

## Riesgos tecnicos

| Riesgo | Impacto | Mitigacion |
| --- | --- | --- |
| Falsos negativos | Se filtran datos sensibles | Ampliar taxonomia y reglas |
| Falsos positivos | Se reduce la utilidad de la consulta | Ajustar decision contextual |
| Posiciones incorrectos | Se reemplaza texto equivocado | Transformar sobre texto original |
| Conjunto de datos pequeno | Evaluacion debil | Crear escenarios anotados y piloto |
| Dependencia de servicios externos | Riesgo de privacidad y costo | Priorizar ejecucion local cuando sea posible |





