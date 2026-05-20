# Escenarios experimentales iniciales

## Proposito

Estos escenarios serviran como banco inicial para probar la capa intermedia y disenar el experimento con usuarios. Todos los datos son ficticios y deben mantenerse asi durante las pruebas piloto.

Cada escenario representa una situacion academica realista en la que un estudiante podria pedir ayuda a un modelo de lenguaje grande.

## Estructura de uso

Para cada escenario se puede pedir al participante:

1. Leer el caso.
2. Preparar un consulta para un modelo de lenguaje grande.
3. Desidentificar manualmente los datos que considere sensibles.
4. Comparar su resultado contra la capa intermedia.

## Escenarios

### Escenario 1: Solicitud de mejora de correo academico

Texto base:

```text
Me llamo Carlos Andres Perez, mi correo es carlos.perez@gmail.com y estudio Ingenieria de Software. Necesito escribirle a la docente Maria Fernanda Lopez porque saque 6.2 en el examen de Seguridad Informatica y quiero pedir recalificacion.
```

Entidades esperadas:

| Texto | Tipo | Sensibilidad |
| --- | --- | --- |
| Carlos Andres Perez | PERSONA | Alta |
| carlos.perez@gmail.com | EMAIL_PERSONAL | Alta |
| Ingenieria de Software | CARRERA | Media |
| Maria Fernanda Lopez | PERSONA | Media/Alta |
| 6.2 | NOTA | Alta |
| Seguridad Informatica | MATERIA | Media |

### Escenario 2: Consulta con cedula

Texto base:

```text
Soy Andrea Salazar y mi cedula es 1723456789. Quiero preguntar al modelo de lenguaje grande como redactar un reclamo porque mi matricula no aparece registrada en el sistema academico.
```

Entidades esperadas:

| Texto | Tipo | Sensibilidad |
| --- | --- | --- |
| Andrea Salazar | PERSONA | Alta |
| 1723456789 | EC_CEDULA | Alta |
| matricula | DATO_ACADEMICO | Media |
| sistema academico | SISTEMA_INSTITUCIONAL | Media |

### Escenario 3: Caso de beca y datos financieros

Texto base:

```text
Mi nombre es Daniela Torres. Recibo una beca por situacion economica y tengo una deuda pendiente de 320 dolares con la universidad. Quiero que ChatGPT me ayude a redactar una solicitud de prorroga de pago.
```

Entidades esperadas:

| Texto | Tipo | Sensibilidad |
| --- | --- | --- |
| Daniela Torres | PERSONA | Alta |
| beca por situacion economica | DATO_FINANCIERO | Critica |
| deuda pendiente de 320 dolares | DATO_FINANCIERO | Critica |
| universidad | INSTITUCION | Media |

### Escenario 4: Informacion de salud

Texto base:

```text
Soy Luis Cardenas, estudiante de sexto semestre. Tengo un certificado medico por ansiedad y necesito pedir una extension para entregar mi proyecto final.
```

Entidades esperadas:

| Texto | Tipo | Sensibilidad |
| --- | --- | --- |
| Luis Cardenas | PERSONA | Alta |
| sexto semestre | DATO_ACADEMICO | Media |
| certificado medico | SALUD | Critica |
| ansiedad | SALUD | Critica |
| proyecto final | DATO_ACADEMICO | Media |

### Escenario 5: Direccion y rutina

Texto base:

```text
Me llamo Kevin Morales. Vivo cerca de la Av. Amazonas y Naciones Unidas y todos los dias salgo a las 6:30 para llegar al campus. Quiero pedirle al modelo de lenguaje grande que me ayude a justificar atrasos frecuentes.
```

Entidades esperadas:

| Texto | Tipo | Sensibilidad |
| --- | --- | --- |
| Kevin Morales | PERSONA | Alta |
| Av. Amazonas y Naciones Unidas | DIRECCION | Alta |
| todos los dias salgo a las 6:30 | RUTINA | Alta |
| campus | UBICACION_INSTITUCIONAL | Media |

### Escenario 6: Correo institucional

Texto base:

```text
Mi usuario institucional es apadilla2026 y mi correo es apadilla@universidad.edu.ec. Necesito redactar un mensaje para soporte porque no puedo ingresar al aula virtual.
```

Entidades esperadas:

| Texto | Tipo | Sensibilidad |
| --- | --- | --- |
| apadilla2026 | USUARIO_INSTITUCIONAL | Alta |
| apadilla@universidad.edu.ec | EMAIL_INSTITUCIONAL | Media/Alta |
| aula virtual | SISTEMA_INSTITUCIONAL | Media |

### Escenario 7: Informacion familiar

Texto base:

```text
Soy Paula Herrera. Mi mama, Monica Herrera, esta enferma y necesito enviar una justificacion para faltar a clases esta semana.
```

Entidades esperadas:

| Texto | Tipo | Sensibilidad |
| --- | --- | --- |
| Paula Herrera | PERSONA | Alta |
| Monica Herrera | PERSONA | Alta |
| mama | RELACION_FAMILIAR | Alta |
| esta enferma | SALUD | Critica |
| faltar a clases esta semana | DATO_ACADEMICO | Media |

### Escenario 8: Practicas preprofesionales

Texto base:

```text
Me llamo Javier Ruiz y hago practicas en Banco Andino. Quiero preguntarle al modelo de lenguaje grande como explicar que no puedo asistir a una reunion porque tuve un problema con informacion de clientes.
```

Entidades esperadas:

| Texto | Tipo | Sensibilidad |
| --- | --- | --- |
| Javier Ruiz | PERSONA | Alta |
| Banco Andino | ORGANIZACION | Media |
| informacion de clientes | DATO_CONFIDENCIAL | Alta |

### Escenario 9: Datos publicos o de baja sensibilidad

Texto base:

```text
Quiero redactar una pregunta para la secretaria academica sobre los horarios de atencion publicados en la pagina institucional de la universidad.
```

Entidades esperadas:

| Texto | Tipo | Sensibilidad |
| --- | --- | --- |
| secretaria academica | DEPENDENCIA | Baja/Media |
| horarios de atencion publicados | DATO_PUBLICO | Baja |
| universidad | INSTITUCION | Baja/Media |

### Escenario 10: Prompt con multiples datos sensibles

Texto base:

```text
Soy Esteban Molina, cedula 1711122233, telefono 0998887776. Necesito escribir una solicitud porque reprobe Calculo II con 4.8 y perdi mi beca.
```

Entidades esperadas:

| Texto | Tipo | Sensibilidad |
| --- | --- | --- |
| Esteban Molina | PERSONA | Alta |
| 1711122233 | EC_CEDULA | Alta |
| 0998887776 | TELEFONO | Alta |
| Calculo II | MATERIA | Media |
| 4.8 | NOTA | Alta |
| perdi mi beca | DATO_FINANCIERO/ACADEMICO | Critica |

## Plantilla de anotacion recomendada

| id_escenario | texto_entidad | tipo_entidad | sensibilidad | peso | debe_transformarse | razon |
| --- | --- | --- | --- | ---: | --- | --- |
| S01 | Carlos Andres Perez | PERSONA | Alta | 3 | Si | Identifica directamente a una persona |

## Pendientes para Iteracion 1

- Aumentar el banco a 20 escenarios.
- Crear version CSV o JSON para evaluacion automatica.
- Validar niveles de sensibilidad con tutor.
- Separar escenarios faciles, medios y ambiguos.





