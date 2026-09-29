# Plan — Carga masiva de asociados

| Unidad | Tamaño | Descripción | Criterios |
|---|---|---|---|
| UT-01 | XS | Definir columnas obligatorias y formato normalizado de fila | AC-01, AC-07 |
| UT-02 | S | Implementar parser CSV | AC-01, AC-07 |
| UT-03 | S | Implementar parser XLSX | AC-01, AC-07 |
| UT-04 | M | Integrar validaciones del dominio para una fila | AC-05, AC-06, AC-09 |
| UT-05 | M | Implementar persistencia parcial fila por fila | AC-03, AC-04 |
| UT-06 | S | Construir resumen de procesamiento | AC-04, AC-08 |
| UT-07 | S | Exponer endpoint y aplicar permisos de administrador | AC-02 |
| UT-08 | M | Agregar pruebas automatizadas de éxito y errores | AC-02, AC-03, AC-04, AC-06, AC-10 |
| UT-09 | XS | Documentar formato de archivo y ejemplos | AC-01, AC-07, AC-08 |

## Orden recomendado

1. UT-01
2. UT-02 y UT-03
3. UT-04
4. UT-05
5. UT-06
6. UT-07
7. UT-08
8. UT-09

## Definición de terminado

Una unidad se considera terminada cuando:

- cumple sus criterios asociados;
- tiene pruebas cuando aplica;
- no duplica reglas existentes;
- pasa lint y suite automatizada;
- actualiza documentación si cambia contrato o comportamiento.
