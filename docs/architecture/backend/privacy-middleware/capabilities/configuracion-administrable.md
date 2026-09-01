# Configuración administrable

## Propósito

La configuración administrable permite ajustar el comportamiento del sistema sin cambiar su contrato semántico ni desplegar lógica nueva. El middleware es dueño de validar, conservar y aplicar esta configuración.

## Capacidades

La administración puede gestionar:

- el modelo de detección seleccionado entre los modelos declarados por el servicio de inferencia;
- el mapeo de categorías nativas de cada modelo hacia la taxonomía canónica;
- los reconocedores estructurales, incluidos patrones, validadores, contexto, confianza y estado;
- los diccionarios, sus entradas, su categoría asociada y su estado;
- el umbral mínimo y la prioridad entre fuentes de detección;
- las reglas que asignan una operación de protección a cada categoría.

## Funcionamiento

La configuración se consulta y modifica mediante una API administrativa bajo `/api/admin`. Esta API permite operar temporalmente desde Postman o la documentación interactiva sin depender de una interfaz administrativa. El procesamiento de interacciones consume posteriormente la configuración válida persistida; el cliente administrativo no participa en dicho procesamiento.

La selección de modelos se limita al catálogo declarado por el servicio de inferencia. Desplegar o retirar modelos pertenece a la infraestructura de inferencia y no a la administración funcional.

## Invariantes

- La taxonomía canónica no se crea, elimina ni renombra desde administración.
- Todo mapeo de modelo apunta a una categoría canónica existente.
- Todo diccionario y reconocedor habilitado produce una categoría canónica existente.
- Las reglas de protección se expresan con categorías canónicas y operaciones soportadas.
- Una regla específica tiene prioridad sobre una regla heredada de una categoría general.
- La configuración inválida no sustituye la última configuración válida usada para procesar interacciones.

## Límites

La administración define qué recursos y reglas utiliza el sistema. No ejecuta modelos, no fusiona detecciones y no transforma texto.

La API administrativa de desarrollo no implementa autenticación, usuarios, roles ni permisos. Esta exposición es adecuada únicamente para el entorno local previsto.
