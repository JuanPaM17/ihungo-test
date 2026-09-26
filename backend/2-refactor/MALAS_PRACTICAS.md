# Backend 2 — Malas prácticas identificadas

Este documento analiza las malas prácticas presentes en `sentimentAnalysis.py`.

La numeración de líneas usada en este documento debe ajustarse al archivo original que se versionará dentro del reto, ya que el enunciado entregado en PDF no conserva una numeración de líneas confiable.

---

## 1. API key definida directamente en el código

**Ubicación:** constructor de `Analytics`, parámetro `key`.

```python
def __init__(
    self,
    path,
    key='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
):
```

### Principio o práctica vulnerada

- Gestión segura de secretos.
- Configuración externa.
- Separation of Configuration from Code.

### Problema

La clave del proveedor de análisis de sentimiento se define directamente como valor por defecto dentro del código fuente.

Aunque el valor mostrado en el ejercicio está oculto con `X`, el diseño permite y fomenta que una credencial real termine almacenada directamente en el repositorio.

### Impacto

- Riesgo de exposición de credenciales.
- Dificulta manejar claves diferentes entre desarrollo, pruebas y producción.
- Obliga a modificar el código para cambiar la configuración.
- Puede provocar que secretos terminen en el historial de Git.

### Mejora

Obtener la clave desde una variable de entorno.

```python
api_key = os.environ["PARALLELDOTS_API_KEY"]
```

---

## 2. La clase `Analytics` tiene demasiadas responsabilidades

**Ubicación:** clase `Analytics`, especialmente `process_file()`.

### Principio o práctica vulnerada

- Single Responsibility Principle (SRP).
- Separation of Concerns.

### Problema

`Analytics` se encarga simultáneamente de:

- comprobar la existencia del archivo;
- abrir el Excel;
- seleccionar la hoja;
- leer celdas;
- llamar al proveedor externo;
- interpretar su respuesta;
- modificar el Excel;
- controlar esperas;
- guardar el archivo.

La lógica de procesamiento, infraestructura y acceso al proveedor están concentradas en una única clase.

### Impacto

- Mayor acoplamiento.
- Código más difícil de probar.
- Cambiar el proveedor de sentimiento afecta la lógica de procesamiento.
- Cambiar el formato de entrada también requiere modificar la misma clase.
- Menor reutilización.

### Mejora

Separar responsabilidades, por ejemplo:

```text
CLI
 ↓
ExcelProcessor
 ↓
SentimentProvider
 ↓
ParallelDotsProvider
```

---

## 3. Dependencia directa de `paralleldots`

**Ubicación:**

```python
paralleldots.set_api_key(self.key)
```

y:

```python
output_sentiment = paralleldots.sentiment(...)
```

### Principio o práctica vulnerada

- Dependency Inversion Principle (DIP).
- Bajo acoplamiento.
- Programar contra abstracciones y no contra implementaciones.

### Problema

La lógica de procesamiento depende directamente de la librería `paralleldots`.

No existe una interfaz que represente genéricamente a un proveedor de análisis de sentimiento.

### Impacto

- Es difícil sustituir ParallelDots por otro proveedor.
- Las pruebas quedan acopladas a un servicio externo.
- Los cambios en la SDK de ParallelDots afectan directamente la lógica principal.

### Mejora

Definir una abstracción como:

```python
from typing import Protocol


class SentimentProvider(Protocol):
    def analyze(self, text: str) -> dict:
        ...
```

y crear posteriormente una implementación específica para ParallelDots.

---

## 4. Configuración repetida de la API key

**Ubicación:**

```python
paralleldots.set_api_key(self.key)
```

aparece antes de abrir el archivo y nuevamente dentro del ciclo.

### Principio o práctica vulnerada

- DRY (Don't Repeat Yourself).
- Evitar operaciones innecesarias.

### Problema

La API key se configura antes de comenzar el procesamiento y vuelve a configurarse en cada iteración.

### Impacto

- Código redundante.
- Hace menos clara la intención del programa.
- Ejecuta una operación innecesaria por cada fila procesada.

### Mejora

Configurar el proveedor una única vez durante su inicialización.

---

## 5. Se obtiene `max_row`, pero no se utiliza

**Ubicación:**

```python
max_row = sheet.max_row
```

seguido por:

```python
for row in range(2, 4):
```

### Principio o práctica vulnerada

- Evitar código muerto.
- Claridad y mantenibilidad.

### Problema

El programa calcula la cantidad total de filas del Excel, pero luego ignora ese valor.

El ciclo está limitado de forma fija a las filas `2` y `3`.

### Impacto

Si el archivo contiene más registros, estos no serán procesados.

Además, la variable `max_row` queda como código innecesario.

### Mejora

Utilizar la cantidad real de filas:

```python
for row in range(2, sheet.max_row + 1):
```

---

## 6. Valores mágicos y configuración hardcodeada

**Ubicación:**

```python
sheet.cell(1, 4)
sheet.cell(1, 5)
sheet.cell(1, 6)

sheet.cell(row, 3)

for row in range(2, 4)
```

### Principio o práctica vulnerada

- Evitar Magic Numbers.
- Configuración externa.
- Mantenibilidad.

### Problema

El programa utiliza directamente números para representar:

- columna de entrada: `3`;
- columnas de salida: `4`, `5`, `6`;
- fila inicial: `2`;
- límite del ciclo: `4`.

No se explica mediante nombres qué representa cada valor.

### Impacto

- El código resulta más difícil de leer.
- Cambiar la estructura del Excel obliga a modificar directamente la implementación.
- Se incrementa el riesgo de introducir errores.

### Mejora

Permitir configurar al menos:

- hoja;
- columna de texto;
- archivo de entrada;
- archivo de salida.

También pueden utilizarse constantes con nombres descriptivos.

---

## 7. Archivo de salida hardcodeado

**Ubicación:**

```python
workbook.save('sentimentAnalysis.xlsx')
```

### Principio o práctica vulnerada

- Configuración externa.
- Reutilización.
- Separation of Concerns.

### Problema

El nombre y ubicación del archivo de salida están definidos directamente dentro de la lógica.

### Impacto

- El usuario no puede elegir el destino del resultado.
- Diferentes ejecuciones pueden sobrescribir el mismo archivo.
- La lógica queda acoplada a un nombre específico.

### Mejora

Recibir el archivo de salida mediante argumentos CLI.

```bash
python -m sentiment.cli \
    --input input.xlsx \
    --output sentimentAnalysis.xlsx
```

---

## 8. Selección fija de la hoja activa

**Ubicación:**

```python
sheet = workbook.active
```

### Principio o práctica vulnerada

- Configuración externa.
- Flexibilidad.

### Problema

Siempre se procesa la hoja activa del documento y no se permite seleccionar una hoja específica.

### Impacto

Si el archivo contiene varias hojas y la hoja requerida no es la activa, se procesarán datos incorrectos.

### Mejora

Permitir seleccionar la hoja mediante un argumento CLI, por ejemplo:

```bash
--sheet comentarios
```

---

## 9. Espera fija de 10 segundos

**Ubicación:**

```python
time.sleep(10)
```

### Principio o práctica vulnerada

- Manejo adecuado de fallos transitorios.
- Resiliencia.
- Evitar esperas arbitrarias.

### Problema

Después de cada solicitud el programa espera siempre 10 segundos, independientemente de si el servicio respondió correctamente o si realmente existe un límite de tasa.

### Impacto

- Hace innecesariamente lento el procesamiento.
- No resuelve correctamente fallos de red.
- No diferencia entre errores temporales y permanentes.
- Una espera fija no constituye una estrategia de reintentos.

### Mejora

Implementar reintentos con backoff.

Por ejemplo:

```text
1 segundo
2 segundos
4 segundos
8 segundos
```

y reintentar únicamente ante errores recuperables.

---

## 10. No existe manejo de excepciones

**Ubicación:** método `process_file()` en general.

### Principio o práctica vulnerada

- Robustez.
- Fail gracefully.
- Manejo explícito de errores.

### Problema

No se manejan posibles excepciones producidas al:

- abrir el archivo;
- leer el Excel;
- llamar al proveedor externo;
- procesar la respuesta;
- guardar el resultado.

### Impacto

Ante cualquier error inesperado, el programa puede finalizar abruptamente sin proporcionar información suficiente sobre la causa.

También podría quedar un procesamiento parcialmente realizado.

### Mejora

Capturar errores en los niveles adecuados y registrar información útil mediante `logging`.

Los errores transitorios del proveedor deberían manejarse mediante reintentos.

---

## 11. Uso de `print()` para observabilidad

**Ubicación:**

```python
print(sheet.cell(row, 3).value)
```

```python
print('Not existe file.')
```

```python
print("Select a file.")
```

### Principio o práctica vulnerada

- Logging estructurado.
- Observabilidad.

### Problema

El programa utiliza `print()` para comunicar información de ejecución y errores.

### Impacto

- No existen niveles como `INFO`, `WARNING` o `ERROR`.
- Es difícil integrar los mensajes con sistemas de monitoreo.
- No hay información consistente de fecha, módulo o contexto.
- Es más difícil diagnosticar problemas en producción.

### Mejora

Utilizar el módulo estándar `logging`.

```python
logger.info("Procesando fila %s", row)
logger.error("No se encontró el archivo: %s", path)
```

---

## 12. Código repetido al procesar el resultado

**Ubicación:** escritura de valores `negative`, `neutral` y `positive`.

```python
round(
    output_sentiment['sentiment']['negative'] * 100,
    3
)
```

```python
round(
    output_sentiment['sentiment']['neutral'] * 100,
    3
)
```

```python
round(
    output_sentiment['sentiment']['positive'] * 100,
    3
)
```

### Principio o práctica vulnerada

- DRY (Don't Repeat Yourself).

### Problema

La misma estructura se repite tres veces cambiando únicamente el nombre de la categoría.

### Impacto

- Mayor cantidad de código.
- Más puntos que modificar.
- Mayor posibilidad de introducir inconsistencias.

### Mejora

Extraer la transformación a una función o representar el resultado mediante una estructura tipada.

---

## 13. Validación insuficiente de la respuesta externa

**Ubicación:**

```python
if 'sentiment' in output_sentiment
```

seguido por accesos como:

```python
output_sentiment['sentiment']['negative']
```

### Principio o práctica vulnerada

- Defensive Programming.
- Validación de datos externos.

### Problema

El código únicamente comprueba que exista la clave `sentiment`.

No valida que dentro de ella existan:

- `negative`;
- `neutral`;
- `positive`.

### Impacto

Una respuesta incompleta o diferente del proveedor puede provocar un `KeyError` y finalizar el proceso.

### Mejora

Validar explícitamente la estructura recibida o convertir la respuesta externa a un modelo interno controlado.

---

## 14. No se validan celdas vacías

**Ubicación:**

```python
str(sheet.cell(row, 3).value)
```

### Principio o práctica vulnerada

- Validación de entradas.

### Problema

El valor se convierte directamente a `str`.

Si la celda está vacía:

```python
None
```

se convierte en:

```text
"None"
```

y podría enviarse al servicio externo como si fuera texto válido.

### Impacto

- Solicitudes innecesarias al proveedor.
- Datos incorrectos.
- Resultados sin significado.

### Mejora

Validar previamente que el contenido exista y sea válido antes de realizar el análisis.

---

## 15. Manejo manual e incorrecto de argumentos CLI

**Ubicación:**

```python
if len(sys.argv) > 1:
    analitycs = (
        Analytics(sys.argv[1])
        if len(sys.argv) <= 2
        else Analytics(sys.argv[2])
    )
```

### Principio o práctica vulnerada

- Uso de herramientas estándar para CLI.
- Claridad.
- Robustez.

### Problema

Los argumentos se procesan manualmente mediante `sys.argv`.

Además, cuando existen más de dos argumentos, el código utiliza:

```python
sys.argv[2]
```

como ruta y deja de utilizar `sys.argv[1]`.

Esto hace que el comportamiento dependa de la cantidad de argumentos de una manera poco intuitiva.

### Impacto

- Fácil uso incorrecto del programa.
- No existe ayuda automática.
- No existe validación clara de parámetros.
- No es posible agregar opciones de manera mantenible.
- Puede terminar procesándose una ruta diferente de la esperada.

### Mejora

Utilizar `argparse` o `typer`.

Por ejemplo:

```text
--input
--output
--sheet
--column
```

---

## 16. Ausencia de type hints

**Ubicación:** clase `Analytics` y sus métodos.

```python
def __init__(self, path, key=...):
```

```python
def process_file(self):
```

```python
def exist_file(self):
```

### Principio o práctica vulnerada

- Tipado estático.
- Documentación del contrato de funciones.

### Problema

No se especifican los tipos de parámetros ni de retorno.

### Impacto

- Menor claridad sobre el contrato de los métodos.
- Algunos errores solo se detectan en ejecución.
- Herramientas como `mypy` no pueden realizar un análisis completo.

### Mejora

Agregar type hints.

```python
def __init__(self, path: str, key: str) -> None:
    ...
```

---

## 17. Nombre de variable incorrecto

**Ubicación:**

```python
analitycs = ...
```

### Principio o práctica vulnerada

- Convenciones de nombres.
- Legibilidad.

### Problema

`analitycs` contiene un error ortográfico.

### Impacto

El impacto funcional es bajo, pero reduce la calidad y legibilidad del código.

### Mejora

Utilizar un nombre correcto y descriptivo:

```python
analytics = ...
```

---

## Resumen

Las principales dificultades del código original están relacionadas con tres aspectos:

1. **Alto acoplamiento:** la lógica depende directamente de ParallelDots y concentra múltiples responsabilidades en `Analytics`.
2. **Configuración rígida:** archivo de salida, hoja, columnas, API key y comportamiento se encuentran definidos dentro del código.
3. **Baja robustez:** no existen reintentos adecuados, manejo de excepciones, logging ni validación suficiente de datos externos.

La refactorización propuesta debe separar el proveedor de sentimiento de la lógica principal, externalizar la configuración, incorporar una CLI formal, implementar reintentos con backoff, utilizar logging y permitir que la lógica pueda probarse sin realizar llamadas reales al proveedor.
