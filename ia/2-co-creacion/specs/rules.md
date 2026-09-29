# Reglas para el asistente — Carga masiva de asociados

1. No modificar contratos existentes sin aprobación humana.
2. No poner lógica de negocio en endpoints o parsers.
3. Reutilizar servicios y validaciones existentes del dominio.
4. No introducir nuevas dependencias sin justificar y pedir aprobación.
5. No hardcodear secretos, credenciales ni rutas locales.
6. No registrar datos sensibles en logs.
7. Mantener compatibilidad con CSV y XLSX.
8. Una fila inválida no debe impedir persistir otras filas válidas.
9. Cada error debe poder asociarse a una fila concreta.
10. No usar IDs internos como requisito del archivo si existe un identificador funcional.
11. Escribir o actualizar pruebas antes de considerar terminada una regla de negocio.
12. Mantener respuestas de error consistentes con el resto de la API.
13. No ejecutar comandos destructivos sin aprobación explícita.
14. Antes de modificar arquitectura, actualizar `design.md` y solicitar aprobación.
15. Si existe ambigüedad en un requisito, preguntar antes de implementar.
16. Las unidades de trabajo deben referenciar criterios de aceptación.
17. Los cambios relevantes deben quedar documentados en `bitacora.md`.
18. La IA propone; la decisión final pertenece al desarrollador.
