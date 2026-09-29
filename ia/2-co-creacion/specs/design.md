# Diseño — Carga masiva de asociados

## Decisión principal

La carga masiva se implementa como un flujo de aplicación que reutiliza las mismas reglas de negocio utilizadas por la creación individual de asociados.

## Arquitectura

```text
HTTP Request
   ↓
Endpoint de carga masiva
   ↓
Parser CSV/XLSX
   ↓
Normalización de fila
   ↓
Servicio de validación / creación
   ↓
Repositorio / ORM
   ↓
Resultado por fila
```

## Decisiones

### Procesamiento fila por fila

Se decidió procesar cada fila de forma independiente.

**Razón:** el requisito de persistencia parcial exige que una fila inválida no invalide automáticamente todo el archivo.

### Reutilización de validaciones

Las reglas de creación de asociados no se duplican dentro del importador.

**Razón:** evita divergencias entre el endpoint individual y el masivo.

### CSV y XLSX

Se soportan ambos formatos mediante parsers separados que producen una representación normalizada común.

**Razón:** separa lectura de archivos de la lógica de dominio.

### Identificadores funcionales

Se evita depender de IDs internos del sistema en el archivo.

**Razón:** hace la importación portable y entendible para usuarios externos.

## Alternativas descartadas

### Transacción global para todo el archivo

Se descartó abortar todo el archivo al primer error.

**Motivo:** contradice AC-03 y dificulta corregir cargas grandes con pocos errores.

### Validaciones duplicadas dentro del parser

Se descartó implementar reglas de negocio directamente en los parsers.

**Motivo:** produciría dos fuentes de verdad.

### Procesamiento asíncrono

Se descartó para esta versión.

**Motivo:** el alcance de la prueba no requiere archivos suficientemente grandes como para justificar colas, workers y seguimiento de jobs.

## Riesgos

- archivos muy grandes;
- formatos de fecha inconsistentes;
- columnas inesperadas;
- duplicados;
- diferencias entre reglas individuales y masivas.

## Mitigaciones

- límites de tamaño documentados;
- normalización explícita;
- validación de encabezados;
- pruebas de duplicados;
- reutilización de servicios de dominio.
