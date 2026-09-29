# Bitácora de co-creación — Carga masiva de asociados

## Entrada 1 — División del problema

**Propuesta de IA:** implementar la carga masiva como una única función que lea el archivo, valide y persista.

**Decisión:** corregida.

**Motivo:** se separó parsing, normalización y reglas de negocio para evitar acoplamiento y permitir reutilizar validaciones existentes.

---

## Entrada 2 — Manejo de errores

**Propuesta inicial:** abortar el procesamiento cuando una fila presentara un error.

**Decisión:** rechazada.

**Motivo:** contradice el criterio de persistencia parcial. Se decidió continuar con las demás filas y reportar errores individualmente.

---

## Entrada 3 — Identificación de asociados

**Propuesta inicial:** usar IDs internos de base de datos dentro del archivo.

**Decisión:** rechazada.

**Motivo:** los IDs internos no son adecuados para archivos preparados por usuarios externos. Se prefirieron identificadores funcionales como email o identificación.

---

## Entrada 4 — Reutilización de reglas

**Propuesta:** validar directamente en el parser campos obligatorios y reglas de dominio.

**Decisión:** parcialmente aceptada.

**Motivo:** el parser valida estructura y formato, pero las reglas de negocio se delegan a los servicios existentes para no duplicarlas.

---

## Entrada 5 — Estrategia de transacciones

**Propuesta:** envolver todo el archivo en una transacción única.

**Decisión:** rechazada.

**Motivo:** una transacción global impediría conservar filas válidas cuando otras fallan. Se mantuvo procesamiento independiente por fila.

---

## Entrada 6 — Formatos soportados

**Propuesta:** implementar primero CSV y dejar XLSX fuera.

**Decisión:** corregida.

**Motivo:** el alcance aprobado incluye ambos formatos; se mantuvieron parsers separados con salida normalizada común.

---

## Entrada 7 — Pruebas

**Propuesta:** probar únicamente un archivo exitoso y un archivo inválido.

**Decisión:** ampliada.

**Motivo:** se añadieron escenarios de permisos, éxito parcial, duplicados y errores por fila porque representan los riesgos principales de la funcionalidad.

---

## Entrada 8 — Validación final

**Acción humana:** se comparó la implementación con el contrato del reto Backend 4 y con los criterios definidos en `requirements.md`.

**Resultado:** se confirmó que la carga masiva mantiene persistencia parcial, reutiliza reglas de negocio y reporta errores individualmente.

---

## Aprendizajes

- Las propuestas de IA son útiles para acelerar estructura y casos, pero deben contrastarse con criterios aprobados.
- Las decisiones que afectan persistencia o reglas de negocio no deben aceptarse solo porque la implementación sea más simple.
- La trazabilidad entre requisito, diseño, plan y pruebas facilita defender por qué una regla existe.
