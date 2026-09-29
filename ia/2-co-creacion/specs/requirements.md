# Especificación — Carga masiva de asociados

## Alcance

Funcionalidad seleccionada para el ejercicio práctico de IA 2: **carga masiva de asociados** del Backend 4.

## Historias de usuario

### HU-01 — Cargar asociados desde archivo

Como administrador,
quiero cargar un archivo CSV o XLSX con múltiples asociados,
para registrar varias personas en una sola operación.

### HU-02 — Conocer errores por fila

Como administrador,
quiero recibir el resultado individual de cada fila,
para corregir únicamente los registros inválidos sin perder los válidos.

## Criterios de aceptación

### AC-01 — Formatos admitidos
Dado un administrador autenticado, cuando envía un archivo `.csv` o `.xlsx` válido al endpoint de carga masiva, entonces el sistema debe procesarlo y devolver un resultado por fila.

### AC-02 — Acceso restringido
Dado un usuario que no tiene rol administrador, cuando intenta ejecutar la carga masiva, entonces la API debe responder `403` y no debe persistir registros.

### AC-03 — Persistencia parcial
Dado un archivo con filas válidas e inválidas, cuando se procesa la carga, entonces las filas válidas deben persistirse aunque existan errores en otras filas.

### AC-04 — Error por fila
Dada una fila inválida, cuando se procesa, entonces la respuesta debe identificar la fila y describir el error correspondiente.

### AC-05 — Reutilización de reglas del dominio
Dada una fila con datos que violan una regla ya existente para creación de asociados, cuando se procesa, entonces debe rechazarse con la misma regla usada por el flujo normal de API.

### AC-06 — Duplicados
Dado un asociado que ya existe según el identificador funcional definido por el sistema, cuando aparece nuevamente en el archivo, entonces la fila debe rechazarse o tratarse según la política aprobada, sin crear duplicados silenciosos.

### AC-07 — Archivo sin columnas requeridas
Dado un archivo al que le faltan columnas obligatorias, cuando se intenta procesar, entonces la API debe responder un error de validación y no debe interpretar columnas incorrectamente.

### AC-08 — Resultado resumido
Al terminar el procesamiento, la respuesta debe incluir la cantidad total de filas procesadas, exitosas y fallidas.

### AC-09 — No depender de IDs internos
Los asociados deben identificarse mediante datos funcionales definidos por el dominio, como email o identificación, y no mediante IDs internos entregados manualmente en el archivo.

### AC-10 — Pruebas automatizadas
La funcionalidad debe contar con pruebas para archivo completamente válido, éxito parcial, archivo inválido, permisos y duplicados.
