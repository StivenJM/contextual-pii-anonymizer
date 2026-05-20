# Taxonomia inicial de informacion sensible

## Proposito

Esta taxonomia permite clasificar informacion sensible que puede aparecer en consultas academicas enviadas a modelos de lenguaje grandes. Sera usada para:

- Anotar escenarios experimentales.
- Evaluar exposicion de informacion.
- Definir reglas de la capa intermedia.
- Calcular metricas de riesgo.

Esta taxonomia es el catalogo objetivo de la tesis. No significa que todos los modelos probados detecten exactamente estas entidades. Los modelos pueden tener etiquetas distintas o cubrir solo una parte del catalogo. Por eso, sus salidas deben normalizarse y complementarse con reglas propias.

## Escala de sensibilidad

| Nivel | Peso | Descripcion |
| --- | ---: | --- |
| Baja | 1 | Dato con bajo riesgo si aparece aislado o es publico |
| Media | 2 | Dato que puede revelar contexto personal, academico o institucional |
| Alta | 3 | Dato que identifica o expone directamente a una persona |
| Critica | 4 | Dato que puede causar dano significativo, discriminacion o fraude |

## Categorias principales

| Categoria | Ejemplos | Sensibilidad base | Accion sugerida |
| --- | --- | --- | --- |
| Identificadores personales | Nombre completo, cedula, pasaporte | Alta | Etiqueta semantica |
| Contacto personal | Correo personal, celular, direccion domiciliaria | Alta | Etiqueta semantica |
| Contacto institucional | Correo universitario, extension, oficina | Media | Evaluar contexto |
| Datos academicos | Matricula, notas, carrera, horario, docente | Media | Evaluar contexto |
| Datos institucionales | Cargo, dependencia, usuario institucional | Media | Evaluar contexto |
| Datos financieros | Cuenta bancaria, tarjeta, deuda, beca, pago | Critica | Etiqueta o bloqueo |
| Datos de salud | Diagnostico, discapacidad, tratamiento, certificado | Critica | Etiqueta o bloqueo |
| Datos familiares | Nombre de familiar, parentesco, direccion familiar | Alta | Etiqueta semantica |
| Datos contextuales | Rutinas, ubicacion frecuente, problemas personales | Media | Evaluar contexto |
| Datos publicos | Nombre de autoridad, telefono publicado | Baja | Mantener o advertir |

## Entidades ecuatorianas prioritarias

| Entidad | Ejemplo | Regla inicial |
| --- | --- | --- |
| Cedula ecuatoriana | `1754650487` | 10 digitos + validacion |
| RUC | `1790012345001` | 13 digitos + validacion pendiente |
| Celular | `0999999999` | 10 digitos, inicia con 09 |
| Telefono convencional | `022999999` | 7 a 9 digitos segun formato |
| Correo institucional | `usuario@universidad.edu.ec` | Dominio institucional |
| Direccion local | `Av. Amazonas y Naciones Unidas` | reconocimiento de entidades nombradas + diccionario |

## Relacion con modelos de reconocimiento de entidades

Las entidades detectadas por modelos son variables. Para cada modelo probado se debe registrar:

- Nombre del modelo.
- Etiquetas declaradas en su configuracion.
- Etiquetas observadas durante pruebas.
- Mapeo hacia la taxonomia comun.
- Entidades no cubiertas por el modelo.
- Entidades cubiertas por reglas propias.

La deteccion por reglas se considera controlada por el proyecto. La deteccion por modelo se considera dependiente del modelo elegido.

## Reglas contextuales iniciales

| Patron contextual | Sensibilidad resultante | Razon |
| --- | --- | --- |
| Persona + cedula | Alta | Identificacion directa |
| Persona + correo personal | Alta | Contacto personal identificable |
| Persona + direccion | Alta | Ubicacion personal |
| Persona + nota o matricula | Alta | Dato academico asociado |
| Persona + salud | Critica | Dato sensible especial |
| Persona + cuenta bancaria | Critica | Riesgo financiero |
| Correo institucional sin caso sensible | Media | Identifica afiliacion |
| Telefono de oficina publicado | Baja o media | Puede ser dato publico |
| Lugar general sin persona | Baja | No identifica directamente |
| Ubicacion frecuente + rutina | Alta | Puede exponer patrones personales |

## Indice de exposicion

Formula inicial:

```text
Indice de Exposicion = suma(peso_sensibilidad de cada entidad expuesta)
```

Ejemplo:

| Entidad expuesta | Nivel | Peso |
| --- | --- | ---: |
| Nombre completo | Alta | 3 |
| Cedula | Alta | 3 |
| Correo personal | Alta | 3 |
| Ciudad | Baja | 1 |

Indice total:

```text
3 + 3 + 3 + 1 = 10
```

## Reglas de anotacion

1. Anotar solo informacion presente en el texto.
2. No inferir datos que no esten explicitamente escritos.
3. Si una entidad cambia de sensibilidad por contexto, registrar la razon.
4. Si una entidad es publica pero se combina con informacion sensible, aumentar sensibilidad.
5. Si existe duda entre dos niveles, elegir el nivel mas alto y registrar observacion.

## Pendientes para Iteracion 1

- Refinar definiciones con bibliografia.
- Agregar ejemplos positivos y negativos por categoria.
- Validar pesos con tutor.
- Crear una plantilla de anotacion.
- Relacionar categorias con normativa ecuatoriana de proteccion de datos.





