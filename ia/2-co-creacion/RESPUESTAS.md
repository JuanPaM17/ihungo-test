# IA 2 — Co-creación en desarrollo guiado por guías

## RESPUESTAS

### 1. ¿Qué diferencia hay entre usar un asistente de IA de forma ad hoc ("vibe coding") y un desarrollo guiado por guías? ¿Qué problemas concretos resuelve el segundo en un equipo?

El uso ad hoc de IA suele partir de una instrucción informal y avanzar por prueba y error: se pide una solución, se copia o adapta el resultado y luego se corrigen problemas sobre la marcha. Puede ser útil para explorar ideas rápidas, pero en un equipo genera riesgos de inconsistencia, decisiones no documentadas, cambios de arquitectura no aprobados y código que funciona sin respetar reglas del proyecto.

En un desarrollo guiado por guías, la IA trabaja dentro de un marco previamente definido: requisitos, diseño, reglas del proyecto, criterios de aceptación, plan de trabajo y puntos de aprobación humana. Esto convierte a la IA en un colaborador controlado y no en una fuente de decisiones autónomas.

Durante esta prueba se vio una diferencia concreta. En DevOps, una solución aparentemente correcta para `runAsNonRoot` falló porque el usuario de la imagen estaba definido por nombre y Kubernetes no podía verificarlo. En lugar de quitar la restricción, se revisó el error, se verificó el UID real de la imagen y se corrigió el manifiesto. Un proceso guiado obliga a validar contra requisitos de seguridad antes de aceptar una solución rápida.

En equipo, este enfoque reduce retrabajo, evita que diferentes desarrolladores o agentes adopten convenciones incompatibles y deja trazabilidad de por qué se tomó cada decisión.

---

### 2. En un ciclo con fases de concepción (Inception), construcción (Construction) y operación (Operations), ¿qué artefactos esperaría que salgan de cada fase y quién debe aprobarlos?

En Inception espero artefactos que definan qué problema se va a resolver y bajo qué restricciones. Como mínimo: historias de usuario, criterios de aceptación, alcance, reglas de negocio, riesgos, decisiones de arquitectura iniciales y preguntas abiertas. La aprobación debe venir del responsable funcional o del dueño del producto para requisitos, y de un referente técnico para decisiones de arquitectura que afecten mantenibilidad, seguridad o integración.

En Construction espero un diseño más concreto, plan de unidades de trabajo, pruebas asociadas a criterios de aceptación, código, documentación técnica y evidencia de validaciones automáticas. La IA puede proponer código o pruebas, pero un desarrollador debe aprobar cambios importantes, especialmente cuando afectan permisos, seguridad, contratos de API o datos.

En Operations espero artefactos relacionados con despliegue, observabilidad, configuración, runbooks, evidencias de salud del sistema y estrategia de rollback. En esta prueba, por ejemplo, los manifiestos k3s, probes, límites de recursos, evidencias de rolling update y el archivo `EVIDENCIAS.md` pertenecen a esa fase.

La aprobación debe depender del riesgo: cambios pequeños pueden pasar con CI y revisión de código; cambios de seguridad, permisos o infraestructura requieren revisión humana explícita. La idea no es añadir burocracia, sino ubicar aprobación donde una decisión equivocada tenga impacto real.

---

### 3. ¿Qué debe contener un archivo de reglas o guía del proyecto y qué no debe contener nunca?

Un archivo como `AGENTS.md`, `CLAUDE.md` o `rules.md` debe contener instrucciones estables que ayuden a cualquier asistente o desarrollador a trabajar de forma consistente. Debe incluir arquitectura esperada, convenciones de nombres, estilo de commits, ubicación de capas, reglas de negocio críticas, estrategia de pruebas, comandos permitidos, restricciones de seguridad y criterios para aceptar o rechazar cambios.

También debe explicar qué fuentes tienen prioridad cuando hay conflicto. Por ejemplo: primero los criterios de aceptación aprobados, luego el diseño vigente y finalmente las sugerencias del asistente. Esto evita que la IA cambie una regla solo porque encontró una implementación alternativa.

No debe contener secretos, tokens, contraseñas, credenciales de bases de datos ni claves de APIs. Tampoco debería guardar información temporal que cambie con frecuencia, como credenciales locales, resultados de una ejecución específica o rutas personales del equipo. Esa información debe ir en variables de entorno, documentación de ejecución o archivos ignorados por Git.

Durante esta prueba una regla útil sería: “No hardcodear secretos; usar `.env.example` y variables de entorno” y otra: “Las cargas masivas deben reutilizar las mismas reglas de negocio del flujo normal”. Estas instrucciones reducen decisiones inconsistentes de la IA y hacen que futuras modificaciones respeten el diseño aprobado.

---

### 4. ¿Cómo redacta un criterio de aceptación para que sea verificable tanto por una persona como por una prueba automática? Escriba dos ejemplos para la regla "el asociado solo puede editar actividades presentes y futuras".

Un criterio de aceptación debe describir una condición observable, con entradas claras y un resultado verificable. Evito expresiones ambiguas como “debe funcionar correctamente” o “debe impedir cambios antiguos”. Prefiero una estructura del tipo Dado/Cuando/Entonces, porque permite convertir el criterio casi directamente en una prueba.

**AC-01 — Edición permitida de actividad futura**

Dado un asociado autenticado relacionado con una actividad cuya fecha de inicio es posterior al momento actual, cuando envía un `PATCH /api/actividades/{id}/` con un cambio válido, entonces la API debe responder `200`, persistir el cambio y devolver la actividad actualizada.

Este criterio puede verificarse manualmente con una petición HTTP y automáticamente creando una actividad futura en una prueba y comprobando el código de respuesta y el estado en base de datos.

**AC-02 — Edición rechazada de actividad pasada**

Dado un asociado autenticado relacionado con una actividad cuya fecha de finalización es anterior al momento actual, cuando intenta modificarla mediante `PATCH`, entonces la API debe responder `403` y la actividad debe conservar exactamente los valores previos.

Este segundo criterio comprueba tanto la autorización como la ausencia de efectos secundarios. Una prueba automática puede guardar el estado inicial, ejecutar la petición y comparar después los campos persistidos. Así el criterio es verificable por una persona y por CI.

---

### 5. Durante la construcción, la IA propone una solución que funciona pero contradice el documento de diseño aprobado. ¿Qué hace: corrige el código, actualiza el diseño o escala la decisión? ¿Con qué criterio?

Primero no aceptaría el código solo porque funciona. El documento de diseño aprobado actúa como contrato técnico hasta que exista una decisión explícita que lo cambie. Compararía la propuesta de la IA con la intención original del diseño y evaluaría por qué existe la contradicción.

Si la IA simplemente ignoró una regla sin aportar una ventaja clara, corregiría el código para volver al diseño aprobado. Si la solución revela que el diseño tiene una limitación real o que una hipótesis inicial era incorrecta, no modificaría silenciosamente el código: propondría actualizar el diseño y pediría aprobación humana antes de continuar.

Escalaría la decisión cuando afecte seguridad, contratos públicos, reglas de negocio, datos persistidos o una decisión arquitectónica compartida por varios módulos.

Un ejemplo de esta prueba fue el uso de `runAsNonRoot`. La salida más simple habría sido quitar esa restricción para que los Pods iniciaran. Técnicamente “funcionaba”, pero contradecía el objetivo de seguridad. Se mantuvo la regla, se investigaron los UID reales y se corrigió el `securityContext`. El criterio fue priorizar el requisito aprobado sobre la solución rápida.

La regla práctica es: el código no redefine el diseño por accidente; si el diseño cambia, debe quedar documentado y aprobado.

---

### 6. ¿Cómo evita que la especificación y el código diverjan con el tiempo? Describa el mecanismo, no la intención.

La forma práctica de evitar divergencia es crear trazabilidad entre requisitos, unidades de trabajo, pruebas y cambios de código. Cada criterio de aceptación debe tener un identificador estable, por ejemplo `AC-01`. El `plan.md` referencia esos criterios desde unidades como `UT-03`, y las pruebas deben indicar qué criterio validan.

Durante una modificación, el flujo sería: primero actualizar requisitos si cambia el comportamiento esperado; después ajustar diseño si cambia la solución; luego modificar plan y finalmente código y pruebas. Un Pull Request no debería aprobarse si cambia comportamiento sin actualizar la especificación correspondiente.

También incluiría una verificación en revisión de código: “¿Este cambio altera un criterio de aceptación o una decisión de diseño?”. Si la respuesta es sí, se exige actualización documental en el mismo PR.

Para la carga masiva de asociados, por ejemplo, el criterio “las filas válidas se guardan aunque otras fallen” debe aparecer en `requirements.md`, estar asociado a una unidad del `plan.md` y tener una prueba automatizada. Si alguien cambia el servicio para usar una transacción global y abortar todo el archivo, CI debería detectar que la prueba ya no cumple el criterio.

Así la documentación deja de ser un archivo estático y se convierte en parte del flujo de cambio.

---

### 7. ¿Qué tamaño debe tener una unidad de trabajo que se delega a un agente de IA? ¿Cómo la divide si el requerimiento original es "implementar la carga masiva de asociados"?

Una unidad delegada a un agente debe ser lo bastante pequeña para tener un objetivo claro, entradas conocidas y una validación concreta. Evitaría tareas como “implementar carga masiva completa”, porque mezclan parsing, validaciones, persistencia, permisos, errores y pruebas. Eso aumenta la probabilidad de que la IA tome decisiones implícitas no aprobadas.

Para “carga masiva de asociados” la dividiría así:

- `UT-01 [S]`: definir contrato de archivo y columnas obligatorias.
- `UT-02 [S]`: implementar parser CSV.
- `UT-03 [S]`: implementar parser XLSX.
- `UT-04 [M]`: validar una fila reutilizando reglas del dominio.
- `UT-05 [M]`: persistir filas válidas sin abortar por filas inválidas.
- `UT-06 [S]`: construir respuesta con resultados y errores por fila.
- `UT-07 [S]`: proteger endpoint para administradores.
- `UT-08 [M]`: pruebas de éxito parcial, archivo inválido y duplicados.
- `UT-09 [S]`: documentación de uso.

Cada unidad tiene criterios asociados y puede revisarse de forma independiente. Esto hace más fácil detectar cuándo la IA se desvía. También permite reemplazar una solución puntual sin rehacer toda la funcionalidad.

Prefiero unidades XS/S/M; una unidad L debería dividirse antes de delegarla, salvo que sea una investigación sin cambios productivos.

---

### 8. ¿En qué momentos del proceso la aprobación humana es innegociable y en cuáles la considera burocracia? Justifique con riesgo e impacto.

La aprobación humana es innegociable cuando la decisión puede cambiar reglas de negocio, permisos, seguridad, datos persistidos, contratos públicos o arquitectura compartida. También antes de acciones destructivas, publicación a producción, cambios de esquema de base de datos y modificación de secretos o infraestructura.

Por ejemplo, en el agente de IA del reto IA 1, cualquier creación, modificación o eliminación de actividades debe requerir confirmación explícita del usuario. Permitir que el modelo ejecute una escritura solo porque “entendió” la intención sería un riesgo directo sobre datos reales.

También considero obligatoria la revisión humana cuando la IA propone una solución que contradice un diseño aprobado o introduce una dependencia nueva.

En cambio, sería burocrático exigir aprobación manual para tareas de bajo riesgo completamente verificables por automatización, como formateo, lint, generación de archivos de cobertura, cambios internos sin efecto funcional o correcciones de documentación menores. Si CI demuestra que el cambio respeta contratos y no altera comportamiento, añadir múltiples aprobaciones no aporta proporcionalmente.

El criterio que uso es riesgo por impacto y reversibilidad. Cuanto más difícil sea revertir una acción o mayor sea el daño posible, más fuerte debe ser el punto de aprobación humana. La meta es control útil, no aprobación por costumbre.

---

### 9. Describa una situación real en la que la IA le entregó código plausible pero incorrecto. ¿Cómo lo detectó y qué cambió después en su forma de trabajar?

Durante DevOps 3, una solución sugerida para el `initContainer` de PostgreSQL configuró un UID que parecía razonable para ejecutar la imagen como usuario no root. El manifiesto era válido y visualmente parecía correcto, pero el Pod quedó en `CreateContainerConfigError`.

En lugar de seguir modificando valores por ensayo y error, revisé `kubectl get events` y encontré que Kubernetes rechazaba el contenedor por la política `runAsNonRoot`. Luego ejecuté la imagen `postgres:16-alpine` para consultar el usuario real y comprobé que `postgres` utilizaba UID/GID `70`. Se corrigió el manifiesto con esos valores reales.

Más adelante ocurrió algo similar con el backend: la imagen declaraba `USER appuser`, pero Kubernetes no podía verificar un nombre no numérico. Se inspeccionó la imagen y se confirmó UID/GID `999`.

Después de esos errores cambié el enfoque: cuando una sugerencia de IA depende de una propiedad del entorno, una imagen, una librería o un contrato externo, ya no acepto valores supuestos. Primero busco evidencia ejecutable: logs, eventos, documentación o inspección directa.

La lección fue que una respuesta plausible no equivale a una respuesta verificada. La IA propone; el entorno real decide si la hipótesis es correcta.

---

### 10. ¿Cómo trabajarían tres desarrolladores y varios agentes de IA sobre la misma especificación sin pisarse? Considere ramas, propiedad del trabajo y revisión.

Partiría de una especificación compartida con criterios numerados y un `plan.md` que divida el trabajo en unidades independientes. Cada unidad tendría un responsable humano, aunque ese desarrollador utilice uno o varios agentes de IA.

Cada desarrollador trabajaría en una rama asociada a una unidad concreta, por ejemplo `feat/UT-04-validacion-filas`. Los agentes no compartirían directamente ramas ni modificarían unidades asignadas a otro responsable. La propiedad sigue siendo humana: el desarrollador decide qué salida de IA entra a su rama.

Los Pull Requests deben indicar qué unidades y criterios implementan. Antes de fusionar, CI valida pruebas y calidad, y otro desarrollador revisa cambios que afecten contratos, seguridad o reglas de negocio.

Para reducir conflictos, las unidades se diseñan con límites claros. Por ejemplo, un desarrollador puede trabajar en parsing CSV/XLSX, otro en validación/persistencia y otro en endpoint y pruebas de integración. Si dos unidades necesitan tocar el mismo archivo central, se acuerda el orden de integración.

Los agentes pueden generar propuestas en paralelo, pero no son dueños de decisiones compartidas. Las decisiones de arquitectura se actualizan en `design.md` y deben aprobarse antes de que varias ramas dependan de ellas. Así se evita que cada agente “invente” su propia versión del sistema.

---

### 11. ¿Qué información del contexto de negocio le daría a un agente al inicio de la sesión de concepción y qué preguntas esperaría que el agente le haga antes de proponer requisitos?

Le daría al agente el objetivo del sistema, actores, reglas de negocio existentes, restricciones de seguridad, contratos de API, fuentes de datos, límites del alcance y ejemplos reales de uso. También explicaría qué decisiones ya están aprobadas y cuáles siguen abiertas.

Para la carga masiva de asociados, el contexto incluiría: solo administradores pueden ejecutarla; se aceptan CSV/XLSX; cada fila representa un asociado; los errores deben reportarse por fila; las filas válidas no deben perderse por errores en otras; y las reglas deben reutilizar las validaciones normales del dominio.

Esperaría que el agente pregunte antes de diseñar: ¿qué columnas son obligatorias?, ¿qué identifica de forma única a un asociado?, ¿qué pasa con duplicados?, ¿se actualiza un asociado existente o se rechaza?, ¿hay límite de tamaño de archivo?, ¿qué formatos de fecha se aceptan?, ¿qué ocurre si faltan columnas?, ¿qué permisos se requieren?, ¿se necesita auditoría?, ¿el procesamiento es síncrono o asíncrono?

Si el agente empieza a proponer endpoints, modelos o librerías antes de resolver esas preguntas, considero que la fase de concepción está incompleta. Un buen agente debe reducir ambigüedad antes de transformar una idea en requisitos.

---

### 12. ¿Cómo combina TDD con un agente de IA? ¿Quién escribe las pruebas, quién la implementación y en qué orden?

Mantengo el orden de TDD: primero comportamiento esperado, luego prueba que falla, después implementación mínima y finalmente refactor. La IA puede ayudar en cualquiera de las fases, pero no debe invertir ese orden.

Para una regla importante prefiero definir personalmente el criterio de aceptación y revisar la prueba antes de implementar. Puedo pedir a la IA que proponga casos límite o que escriba una primera versión del test, pero la prueba debe representar el contrato aprobado, no la implementación que la IA quiere construir.

Una vez que la prueba falla por la razón correcta, la IA puede proponer la implementación mínima. Después se ejecuta la suite y, si pasa, se revisa si el código puede simplificarse sin cambiar comportamiento.

Esto se aplicó conceptualmente en Backend 3, donde se buscó que el historial mostrara pruebas antes de las implementaciones de números bouncy. En Backend 4 el mismo principio es especialmente importante para permisos y reglas de solapamiento.

No considero correcto pedirle al agente “implementa esto y crea tests que pasen”, porque puede escribir pruebas adaptadas a su propia solución. Primero se fija el contrato; después la implementación debe satisfacerlo. El humano conserva el control sobre qué comportamiento se considera correcto.

---

### 13. ¿Qué controles aplica antes de fusionar código generado por IA? Distinga los automatizados de los humanos.

Los controles automatizados incluyen lint, type checking cuando aplica, pruebas unitarias, pruebas de integración, cobertura mínima, validación de migraciones, análisis de dependencias, escaneo de vulnerabilidades y build reproducible. También verifico que no se hayan añadido secretos ni archivos que deban estar ignorados.

En esta prueba, por ejemplo, el pipeline de Backend 4 ejecuta lint, pruebas y cobertura, mientras DevOps 1 añade build de imagen y escaneo con Trivy. Esos controles reducen el riesgo de integrar cambios que ni siquiera funcionan o introducen vulnerabilidades conocidas.

Los controles humanos se centran en aspectos que CI no comprende bien: si el cambio respeta la intención del requisito, si introduce acoplamiento innecesario, si modifica permisos de forma correcta, si la solución contradice el diseño, si la documentación sigue siendo válida y si una dependencia nueva está justificada.

También reviso especialmente cualquier salida de IA que toque seguridad, autenticación, SQL, manejo de archivos, datos sensibles o infraestructura.

No fusionaría código solo porque “todos los tests pasan”. Los tests demuestran lo que fue probado, no que el requisito estuviera bien interpretado. La revisión humana debe confirmar que las pruebas representan el comportamiento correcto y que no faltan escenarios relevantes.

---

### 14. ¿Cómo evita que un agente exponga secretos, introduzca dependencias no aprobadas o ejecute comandos destructivos?

Primero establezco reglas explícitas: los secretos nunca se escriben en código, prompts versionados, logs ni archivos del repositorio. Se usan variables de entorno, `.env` ignorado y `.env.example` sin valores reales. Además, los logs deben sanitizar tokens y headers de autorización.

Para dependencias, el agente puede proponer una librería, pero no debería instalarla automáticamente si no está aprobada. La propuesta debe incluir motivo, mantenimiento, licencia, impacto en tamaño y alternativa sin dependencia nueva. El humano decide.

Para comandos destructivos, la guía debe prohibir acciones como borrar bases de datos, limpiar volúmenes, hacer `git reset --hard`, eliminar ramas remotas o modificar secretos sin confirmación. Los agentes deberían operar con permisos mínimos y, cuando sea posible, en entornos aislados.

Durante DevOps 3 se aplicó una variante de este principio: los secretos reales de Kubernetes se crearon localmente y no se almacenaron en YAML versionado. También se evitó imprimir valores sensibles al verificar el Secret.

Adicionalmente, revisaría `git diff` antes de commit, usaría escaneo de secretos en CI si está disponible y mantendría las credenciales de proveedores fuera de los traces de observabilidad. El control combina reglas, permisos mínimos y revisión humana.

---

### 15. Seis meses después, alguien pregunta por qué una regla de negocio está implementada de cierta forma. ¿Dónde debería encontrar la respuesta y cómo garantiza que exista?

La respuesta no debería depender de recordar una conversación con la IA. Debe quedar en artefactos versionados junto al código.

Primero buscaría el criterio de aceptación en `requirements.md`. Ahí se explica qué comportamiento debía cumplirse. Luego revisaría `design.md` para entender la decisión técnica, alternativas descartadas y razón de la elección. `plan.md` conecta esa decisión con la unidad de trabajo que la implementó. Finalmente, el historial de Git y el Pull Request muestran qué código cambió y qué revisión recibió.

Si durante el proceso hubo una propuesta de IA rechazada o una corrección relevante, también debe aparecer en `bitacora.md`.

Para garantizar que esta información exista, hago que la trazabilidad sea parte de la definición de terminado: una unidad no se considera completa si cambia una regla sin actualizar requisitos/diseño y sin pruebas asociadas.

Por ejemplo, la decisión de que una carga masiva guarde filas válidas aunque otras fallen debería encontrarse como criterio de aceptación, como decisión explícita de diseño y como prueba automatizada. Si seis meses después alguien propone envolver todo el archivo en una única transacción y abortar ante el primer error, la documentación permite explicar inmediatamente por qué eso contradice el comportamiento aprobado.
