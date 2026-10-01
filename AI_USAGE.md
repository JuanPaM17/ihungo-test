# AI Usage

## Backend
###  Backend 1 — Análisis de arquitectura

#### Herramientas utilizadas
- Claude
- ChatGPT

#### Uso de IA
Se utilizó Claude como apoyo para inspeccionar la estructura del repositorio `app-back` e identificar:
- ubicación de endpoints;
- distribución de la lógica de negocio;
- responsabilidades de paquetes;
- relaciones entre clases de `diagnosis`;
- riesgos de arquitectura;
- posibles incompatibilidades con Python 3.12 y Django 5.x.

Se utilizó ChatGPT para organizar los hallazgos, contrastarlos con los requisitos del reto y estructurar el documento `ANALISIS.md`.

#### Decisiones y validaciones propias
- Se revisaron los archivos del repositorio antes de aceptar las conclusiones.
- Se ajustó la clasificación de capas para reflejar la mezcla real entre serializers, modelos y viewsets.
- Se seleccionaron los riesgos finales priorizando seguridad, mantenibilidad y migración.
- Se revisaron y ajustaron los diagramas a partir del código revisado.

### Backend 2 — Refactorización de código

#### Herramientas utilizadas
- Claude
- ChatGPT

#### Uso de IA
Se utilizó Claude como apoyo para diseñar e implementar la refactorización del script `sentimentAnalysis.py`, especialmente en:

- separación de responsabilidades;
- definición de una interfaz `SentimentProvider` mediante `Protocol`;
- creación de un proveedor concreto para ParallelDots;
- desacoplamiento entre la lógica de procesamiento y el proveedor externo;
- configuración mediante variables de entorno y argumentos CLI;
- implementación de reintentos con exponential backoff;
- uso de `logging`;
- incorporación de type hints;
- configuración de `ruff`, `mypy` y `pytest`;
- creación de dobles de prueba para evitar llamadas reales al servicio de ParallelDots.

Se utilizó ChatGPT para revisar los requisitos del reto, identificar malas prácticas del código original, definir la estructura del refactor y validar que la propuesta cubriera los puntos exigidos en la prueba.

#### Decisiones y validaciones propias
- Se decidió separar el archivo de entrada y el archivo de salida para evitar sobrescribir el Excel original y cumplir con la configuración requerida por CLI.
- Se mantuvo la lógica de procesamiento independiente de ParallelDots mediante inyección de dependencias.
- Se optó por `Protocol` en lugar de una clase abstracta para mantener una interfaz simple y flexible.
- Se revisó que el `processor` no tuviera dependencia directa del SDK de ParallelDots.
- Se decidió utilizar dobles de prueba para validar el procesamiento sin requerir API key ni conexión a internet.
- Se verificó que la refactorización conservara el comportamiento funcional del script original, pero eliminando valores fijos, esperas constantes y dependencias directas.

### Backend 3 — Algoritmia: números bouncy

#### Herramientas utilizadas
- Claude
- ChatGPT

#### Uso de IA
Se utilizó Claude como apoyo para estructurar el desarrollo del reto con enfoque TDD, incluyendo:

- definición inicial de casos de prueba para números increasing, decreasing y bouncy;
- validación de los casos obligatorios `50% -> 538` y `90% -> 21780`;
- organización de las implementaciones independientes en Python y TypeScript;
- creación de las funciones equivalentes en ambos lenguajes;
- preparación de las interfaces CLI;
- revisión de casos inválidos para porcentajes fuera del rango permitido;
- apoyo en la configuración de `pytest` y `vitest` o `jest`.

Se utilizó ChatGPT para revisar los requisitos del reto, definir una estrategia de commits que evidenciara TDD y validar que la comparación de la proporción se realizara con aritmética entera en lugar de punto flotante.

#### Decisiones y validaciones propias
- Se decidió escribir y versionar primero las pruebas antes de implementar el algoritmo, para que el enfoque TDD quedara visible en el historial de Git.
- Se mantuvieron implementaciones independientes en Python y TypeScript, evitando compartir lógica entre ambos lenguajes.
- Se utilizó aritmética entera para comparar la proporción de números bouncy y evitar errores de precisión.
- Se revisaron manualmente los casos `50% -> 538` y `90% -> 21780` antes de usar el resultado de `99%`.
- Se decidió mantener una solución iterativa simple y legible, evitando optimizaciones prematuras.
- Se midió el tiempo de ejecución de cada implementación para documentarlo posteriormente en el `README.md`.

### Backend 4 — API REST de asignación de actividades

#### Herramientas utilizadas
- Claude
- ChatGPT

#### Uso de IA
Se utilizó Claude como apoyo para construir el reto de forma incremental, dividiendo la implementación en fases pequeñas y verificables.

El apoyo de Claude se utilizó principalmente en:

- creación de la estructura base del proyecto con Django REST Framework;
- configuración de PostgreSQL y Docker Compose;
- implementación del endpoint de salud;
- creación del usuario personalizado con autenticación por correo;
- integración de JWT con access y refresh token;
- definición de los modelos de dominio;
- implementación del CRUD de asociados y actividades;
- creación de filtros por rango de fechas;
- separación de lógica de negocio, serializers, permisos y servicios;
- implementación de reglas de fechas y detección de solapamientos;
- implementación de permisos para administradores y asociados;
- creación del flujo de solicitud pública de registro;
- aprobación y rechazo de solicitudes desde Django Admin;
- implementación de carga masiva de asociados y actividades mediante CSV y Excel;
- validación fila por fila sin abortar registros válidos;
- configuración de OpenAPI con `drf-spectacular`;
- configuración de Gunicorn y Nginx;
- configuración de archivos estáticos y variables de entorno;
- creación y ajuste del pipeline de GitLab CI;
- apoyo en la creación de pruebas automatizadas y verificación de cobertura.

Se utilizó ChatGPT para:

- revisar los requisitos del enunciado y dividir el reto en fases de implementación;
- definir el orden de trabajo para evitar implementar toda la solución de una sola vez;
- proponer una estrategia de commits pequeños y descriptivos;
- definir qué funcionalidades debían probarse antes de continuar con la siguiente fase;
- revisar las reglas de negocio y permisos obligatorios;
- validar que la arquitectura propuesta cubriera los requisitos de separación por capas y principios SOLID;
- preparar una lista final de verificación contra el contrato mínimo de la API;
- revisar que el proyecto pudiera ejecutarse de forma reproducible mediante Docker.

#### Decisiones y validaciones propias
- Se eligió Django REST Framework por su integración con Django Admin, ORM, migraciones, autenticación y permisos.
- Se decidió implementar el reto por fases para poder probar cada bloque antes de continuar con el siguiente.
- Se utilizó un modelo de usuario personalizado con `email` como identificador principal.
- Se verificó manualmente el flujo de autenticación JWT comprobando la generación de tokens `access` y `refresh`.
- Se decidió asignar automáticamente el creador de una actividad desde `request.user` y no confiar en un valor enviado por el cliente.
- Se mantuvo la lógica de negocio fuera de los endpoints, usando servicios y permisos para reducir el acoplamiento.
- Se aplicó la regla de solapamiento mediante comparación de rangos de fechas y se excluyó la propia actividad durante actualizaciones.
- Se decidió que una actividad que termina exactamente cuando otra comienza no se considera solapada.
- Se mantuvieron las actividades pasadas como solo lectura para asociados.
- Se aplicó visibilidad de actividades según creador o relación con el asociado.
- Se decidió que las cargas masivas debían reutilizar las mismas reglas de negocio de la API normal, evitando duplicar validaciones.
- Se decidió identificar asociados en cargas masivas mediante datos funcionales como correo o identificación, evitando depender de ids internos.
- Se mantuvo el endpoint de registro como público y las solicitudes en estado pendiente hasta ser procesadas por un administrador.
- Se decidió usar Nginx como reverse proxy y Gunicorn como servidor de aplicación para la configuración de producción.
- Se revisó que los secretos y configuraciones sensibles se manejaran mediante variables de entorno y que `.env` no se versionara.
- Se configuró el pipeline de GitLab para validar lint, pruebas, cobertura y build.
- Se revisó el proyecto al final contra los endpoints, reglas de negocio, permisos, carga masiva, OpenAPI, Docker, CI y documentación requeridos por el reto.

## DevOps
### DevOps 1 — GitHub Actions → Docker Hub

#### Herramientas utilizadas
- Claude
- ChatGPT

#### Uso de IA
Se utilizó Claude como apoyo para implementar y ajustar el reto DevOps 1, especialmente en:

- revisión y mejora del `Dockerfile` del Backend 4;
- conversión del build a una estrategia multi-stage;
- creación de un usuario no root para ejecutar la aplicación dentro del contenedor;
- definición y ajuste de `.dockerignore`;
- creación del workflow `.github/workflows/ci-dockerhub.yml`;
- configuración de jobs separados para calidad y construcción;
- ejecución de `ruff` y pruebas antes del build;
- configuración de Docker Buildx;
- autenticación con Docker Hub mediante secrets;
- generación de etiquetas trazables por rama, versión semántica y SHA;
- integración de Trivy para escaneo de vulnerabilidades;
- generación y carga de resultados SARIF en GitHub Security;
- publicación de imágenes en Docker Hub solo desde `main` y tags;
- uso de caché para optimizar builds sucesivos;
- corrección de versiones de actions que inicialmente producían errores en el pipeline.

Se utilizó ChatGPT para:

- revisar el documento de la prueba DevOps y separar los requisitos obligatorios de las recomendaciones adicionales;
- identificar los defectos intencionales presentes en las definiciones de referencia;
- definir el orden de implementación y validación del reto;
- orientar la creación del espejo del repositorio en GitHub;
- configurar correctamente los secrets `DOCKERHUB_USERNAME` y `DOCKERHUB_TOKEN`;
- validar el proceso de publicación manual inicial en Docker Hub;
- revisar los errores del workflow relacionados con Trivy y las actions de seguridad;
- validar las etiquetas publicadas en Docker Hub;
- estructurar el contenido de `devops/EVIDENCIAS.md`;
- definir qué capturas y enlaces eran realmente necesarios para evidenciar el reto.

#### Decisiones y validaciones propias
- Se mantuvo GitLab como repositorio principal y se creó un espejo en GitHub únicamente para ejecutar GitHub Actions.
- Se validó manualmente `docker build` y `docker push` antes de automatizar la publicación mediante CI.
- Se decidió utilizar una imagen Docker multi-stage para reducir el contenido de la imagen final.
- Se decidió ejecutar la aplicación con un usuario no root para reducir privilegios dentro del contenedor.
- Se verificó que `.env`, archivos de Git, cachés y otros archivos innecesarios quedaran excluidos mediante `.dockerignore`.
- Se decidió que los Pull Requests ejecutaran lint, pruebas, build y escaneo, pero no publicaran imágenes.
- Se condicionó el login a Docker Hub para evitar utilizar credenciales durante ejecuciones de Pull Request.
- Se definió que el job `Build · Scan · Push` dependiera de `Lint & Tests`, evitando publicar una imagen si las validaciones de calidad fallan.
- Se decidió no utilizar `latest` como etiqueta principal y mantener etiquetas trazables por rama, versión semántica y commit.
- Se utilizaron las etiquetas `main`, `1.0.0`, `1.0` y `sha-6568187` para comprobar la trazabilidad de las imágenes publicadas.
- Se creó y publicó el tag Git `v1.0.0` para comprobar que el workflow también se ejecutara correctamente ante versionado semántico.
- Se verificó en Docker Hub que las imágenes correspondientes a `main`, versión semántica y SHA fueran publicadas correctamente.
- Se corrigieron errores reales encontrados durante la ejecución del pipeline, incluyendo versiones inválidas o incompatibles de las actions de Trivy.
- Se revisó que los secretos de Docker Hub permanecieran únicamente en GitHub Secrets y no fueran incluidos en el repositorio ni en el workflow.
- Se documentaron en `devops/EVIDENCIAS.md` las ejecuciones exitosas, etiquetas publicadas y defectos corregidos.

### DevOps 3 — Despliegue en k3s

#### Herramientas utilizadas
- Claude
- ChatGPT

#### Uso de IA
Se utilizó Claude como apoyo para estructurar e implementar el reto DevOps 3 de forma incremental, especialmente en:

- definición de la estructura de manifiestos de Kubernetes;
- creación de `namespace.yaml`;
- creación de `configmap.yaml`;
- creación de `secret.yaml` con placeholders seguros;
- definición de la estrategia para crear el Secret real desde CLI sin versionar credenciales;
- creación del manifiesto de PostgreSQL dentro del clúster;
- configuración de `StatefulSet`, `PersistentVolumeClaim` y Service interno para PostgreSQL;
- creación y ajuste de `deployment.yaml` para el backend;
- configuración de dos réplicas;
- configuración de estrategia `RollingUpdate`;
- uso de imagen con etiqueta inmutable basada en SHA;
- configuración de `readinessProbe` y `livenessProbe`;
- definición de `requests` y `limits` de CPU y memoria;
- uso de `ConfigMap` y `Secret` mediante `configMapKeyRef` y `secretKeyRef`;
- configuración de `securityContext` y ejecución no root;
- creación del init container `wait-for-postgres`;
- creación del `Service` de tipo `NodePort`;
- preparación de comandos de validación y evidencias para el despliegue.

Se utilizó ChatGPT para:

- revisar los requisitos del documento DevOps antes de implementar cada fase;
- dividir DevOps 3 en pasos pequeños para evitar aplicar todos los manifiestos de una sola vez;
- orientar la instalación y configuración de k3s en WSL2;
- configurar `kubectl` para trabajar sin `sudo`;
- revisar la estrategia de separación entre ConfigMap y Secret;
- corregir la forma de crear secretos reales sin escribir credenciales directamente en archivos versionados;
- revisar errores reales producidos durante la ejecución del Deployment;
- analizar `CreateContainerConfigError` y eventos de Kubernetes;
- identificar el conflicto entre `runAsNonRoot` y el init container basado en `postgres:16-alpine`;
- verificar el UID/GID real del usuario `postgres` dentro de la imagen y ajustar el `securityContext`;
- identificar el conflicto entre `runAsNonRoot` y el usuario no numérico `appuser` de la imagen del backend;
- verificar el UID/GID real de `appuser` y `appgroup` y ajustar el `securityContext`;
- analizar los reinicios de los Pods mediante logs anteriores;
- identificar que las probes fallaban por `Django DisallowedHost`;
- proponer el uso de `Host: localhost` en las probes en lugar de abrir `ALLOWED_HOSTS`;
- validar que las dos réplicas alcanzaran estado `1/1 Running`;
- validar el `Service` NodePort y el endpoint `/api/health/`;
- definir la estrategia para demostrar un rolling update sin caída;
- revisar qué capturas y resultados debían conservarse en `EVIDENCIAS.md`;
- diferenciar defectos de la definición de referencia de problemas reales encontrados durante la implementación.

#### Decisiones y validaciones propias
- Se decidió ejecutar k3s localmente sobre WSL2 en lugar de utilizar un VPS o una máquina virtual separada.
- Se verificó manualmente que el nodo `madrigal` quedara en estado `Ready`.
- Se configuró `kubectl` para utilizar una copia local del kubeconfig y poder operar sin `sudo`.
- Se decidió utilizar un namespace dedicado llamado `ihungo`.
- Se separó la configuración no sensible en `ConfigMap` y los valores sensibles en `Secret`.
- Se decidió no aplicar credenciales reales desde un archivo `secret.yaml` versionado.
- Se generaron los valores sensibles reales localmente y se creó `ihungo-secret` mediante `kubectl`, manteniendo los valores fuera de Git.
- Se decidió desplegar PostgreSQL dentro del mismo clúster para que la solución fuera reproducible y no dependiera de una base externa.
- Se utilizó almacenamiento persistente para PostgreSQL mediante PVC.
- Se decidió utilizar la imagen `docker.io/juanpablomc/ihungo-backend:sha-6568187` para mantener trazabilidad e inmutabilidad.
- Se configuraron dos réplicas del backend para permitir la demostración de actualizaciones sin caída.
- Se configuró `RollingUpdate` con `maxUnavailable: 0` y `maxSurge: 1`.
- Se mantuvo `runAsNonRoot: true` en lugar de eliminar la restricción cuando aparecieron errores de seguridad.
- Se verificó directamente dentro de `postgres:16-alpine` que el usuario `postgres` utiliza UID/GID `70`, y se configuró explícitamente en el init container.
- Se verificó directamente sobre la imagen del backend que `appuser` y `appgroup` utilizan UID/GID `999`, y se configuraron explícitamente en el contenedor.
- Se mantuvo el init container `wait-for-postgres` para evitar que Django iniciara antes de que PostgreSQL aceptara conexiones.
- Se verificó que `postgres-svc:5432` aceptara conexiones antes de continuar con el arranque del backend.
- Se mantuvieron `readinessProbe` y `livenessProbe` sobre el endpoint real `/api/health/`.
- Se decidió configurar `Host: localhost` en las probes en lugar de usar `ALLOWED_HOSTS=*`.
- Se verificó manualmente que ambas réplicas del backend llegaran a `1/1 Running` y que el Deployment quedara `2/2 Ready`.
- Se expuso el backend mediante un `Service` de tipo `NodePort` en el puerto `30080`.
- Se verificó manualmente desde WSL2 que `curl http://localhost:30080/api/health/` respondiera `{"status":"ok"}`.
- Se realizó un rolling update forzado mediante un cambio en el Pod template para demostrar el comportamiento del Deployment sin necesidad de cambiar la imagen.
- Durante el rolling update se mantuvo un health check continuo y se verificó que las respuestas HTTP permanecieran en `200`.
- Se conservaron capturas del namespace, ConfigMap, Secret, Pods, Service NodePort, health check, rolling update y continuidad del servicio para documentarlas en `EVIDENCIAS.md`.

## IA

# AI Usage — IA 1

## IA 1 — Agente conversacional con LLM

### Herramientas utilizadas

- Claude
- ChatGPT

### Uso de IA

Se utilizó Claude como apoyo principal para inspeccionar, adaptar y evolucionar un agente conversacional existente construido con FastAPI, LangGraph y herramientas dinámicas, con el objetivo de alinearlo con los requisitos del reto IA 1.

El apoyo de Claude se utilizó especialmente en:

- auditoría inicial de la arquitectura existente del agente;
- identificación de las diferencias entre las implementaciones V1 y V2;
- revisión del flujo de V2 basado en supervisor, agentes especializados, evaluator y summarizer;
- identificación de riesgos relacionados con JWT, sesiones, prompts, herramientas y trazas;
- eliminación de exposición del JWT en logs, respuestas HTTP, prompts y metadata de LangSmith;
- separación entre autenticación mediante JWT y sesión conversacional mediante `session_id`;
- adaptación del endpoint para utilizar `X-Session-Id`;
- implementación de una abstracción `LLMProvider`;
- creación de adaptadores para OpenAI y Gemini;
- parametrización del proveedor y modelos mediante variables de entorno;
- adaptación y registro de las herramientas requeridas por el reto;
- creación de la herramienta `consultar_disponibilidad`;
- mejora de `buscar_asociados` para soportar búsquedas explícitas;
- incorporación y ampliación de herramientas para consultar y gestionar asociados;
- revisión de schemas tipados para function calling;
- integración de nuevas herramientas con los agentes especializados;
- incorporación de reglas de confirmación antes de operaciones de creación, actualización y eliminación;
- definición de comportamiento ante datos ambiguos o incompletos;
- mejora del manejo de fechas relativas utilizando `America/Bogota`;
- fortalecimiento de prompts frente a prompt injection proveniente de datos externos;
- protección adicional del evaluator y summarizer frente a contenido no confiable;
- incorporación de streaming mediante SSE;
- diseño de observabilidad estructurada por turno;
- revisión de límites de ejecución, timeouts y rate limiting;
- diseño y creación de pruebas con proveedores y backend simulados;
- preparación del conjunto de evaluaciones del agente con casos de ambigüedad y prompt injection;
- adaptación del CLI conversacional para manejar autenticación, sesión y renovación de tokens;
- revisión del flujo de permisos entre administradores y asociados.

Se utilizó ChatGPT como apoyo para revisar continuamente los requisitos del documento oficial, contrastarlos con la implementación existente y dividir la adaptación del agente en fases pequeñas y verificables.

ChatGPT se utilizó principalmente para:

- identificar qué requisitos eran obligatorios y cuáles eran mejoras adicionales;
- revisar la auditoría inicial realizada sobre el agente;
- definir el orden de implementación de seguridad, providers, tools, confirmación, fechas, streaming, observabilidad y pruebas;
- revisar los resultados obtenidos después de cada fase antes de continuar;
- detectar que el `session_id` no debía depender directamente del JWT;
- proponer la separación entre autenticación y sesión conversacional;
- revisar el diseño de las tools requeridas por el reto;
- recomendar trasladar reglas de negocio de disponibilidad al Backend 4 en lugar de concentrarlas dentro de la tool;
- revisar las reglas de confirmación antes de operaciones de escritura;
- revisar el tratamiento de fechas ambiguas y relativas;
- revisar los vectores de prompt injection en el agente, evaluator y summarizer;
- definir casos de prueba y escenarios de evaluación;
- revisar el uso de OpenAI y Gemini frente al requisito de abstracción del proveedor;
- preparar la estrategia del cliente CLI con manejo de JWT, refresh token y `session_id`;
- revisar la relación entre usuarios autenticados, administradores, asociados y actividades;
- validar que la API siguiera siendo la autoridad final de permisos;
- analizar errores reales observados en LangSmith, logs y Backend 4 durante pruebas end-to-end.

### Decisiones y validaciones propias

- Se decidió mantener V2 como implementación principal porque era la versión más estable y completa del agente existente.
- Se decidió conservar V1 como alternativa simple en lugar de eliminarla durante la adaptación.
- Se rechazó la propuesta inicial de simplificar V2 a un único agente, ya que el reto no exige una arquitectura interna específica y la implementación con supervisor, agentes especializados, evaluator y summarizer ya funcionaba correctamente.
- Se decidió mantener OpenAI como proveedor activo durante las validaciones porque se disponía de credenciales para este proveedor. El adaptador para Gemini quedó implementado mediante la misma abstracción, pero no se realizaron llamadas reales a Gemini al no disponer de credenciales.
- Se rechazó utilizar el JWT directamente como `thread_id` o identificador de conversación.
- Se descartó derivar el `session_id` mediante un hash del JWT porque un refresh del access token cambiaría la sesión conversacional.
- Se decidió separar completamente ambos conceptos: JWT para autenticación y autorización; `session_id` para identificar la conversación.
- Se configuró el agente para recibir `X-Session-Id` de forma independiente del JWT y generar un UUID cuando el cliente no lo proporciona.
- Se mantuvo el JWT únicamente dentro del contexto interno para que las tools pudieran utilizar los permisos reales del usuario sin exponer el token al modelo.
- Se revisó que el JWT no quedara incluido en prompts, respuestas HTTP, logs o metadata de LangSmith.
- Se corrigió la duplicación `Bearer Bearer` centralizando la normalización del token antes de construir el header `Authorization`.
- Se decidió mantener Backend 4 como autoridad de permisos y reglas de negocio.
- Para la consulta de disponibilidad se decidió mover la lógica principal al Backend 4 y dejar la tool del agente como consumidora de esa funcionalidad.
- Se decidió que `buscar_asociados` realizara una búsqueda explícita y no delegara al modelo el filtrado de listas grandes.
- Se amplió el soporte de asociados manteniendo el control de creación, actualización y eliminación en usuarios con permisos administrativos.
- Se mantuvo la confirmación humana como requisito antes de ejecutar operaciones de creación, modificación o eliminación.
- Se definió que un resultado de una tool, una descripción almacenada en base de datos o cualquier otro dato externo nunca puede contar como confirmación del usuario.
- Se decidió tratar los resultados de tools y Backend 4 como datos no confiables.
- Se identificó que el evaluator era especialmente sensible a prompt injection por la interpolación de entradas y salidas dentro de su prompt, por lo que se reforzó la delimitación entre instrucciones y datos.
- Se decidió utilizar `America/Bogota` como referencia única para fechas relativas.
- Se evitó confiar en la fecha u hora implícita del modelo y se mantuvo una herramienta determinista para obtener la fecha actual.
- Se definió que expresiones ambiguas como una hora sin AM/PM, múltiples asociados con el mismo nombre o varias actividades coincidentes debían generar una pregunta de aclaración en lugar de una suposición.
- Se decidió conservar el endpoint JSON existente y agregar SSE como mecanismo adicional de streaming.
- Se mantuvo LangSmith para trazabilidad y se complementó con observabilidad estructurada local, evitando registrar JWT, API keys, prompts completos o datos sensibles innecesarios.
- Se revisaron los timeouts existentes del LLM y de las llamadas HTTP y se decidió no introducir circuit breakers ni reintentos complejos para esta prueba.
- Se decidió utilizar proveedores simulados y mocks para las pruebas automatizadas, evitando llamadas reales a OpenAI, Gemini o Backend 4 durante CI.
- Se separaron conceptualmente las pruebas automatizadas de las evaluaciones del agente: tests con proveedores simulados para validar comportamiento determinista y evals con proveedor real para medir comportamiento, herramientas utilizadas y tasa de acierto por categoría.
- Se decidió implementar un CLI conversacional como cliente de prueba, manteniendo `access token`, `refresh token` y `session_id` como conceptos separados.
- Se definió que el CLI conservara el mismo `session_id` durante la conversación incluso si el access token debía renovarse.
- Se revisó la diferencia funcional entre administrador y asociado y se mantuvo la API como autoridad para responder `403` cuando una operación excede los permisos del usuario autenticado.
- Se revisaron manualmente los cambios después de cada fase antes de continuar con la siguiente, en lugar de aplicar una refactorización completa del agente de una sola vez.

### IA 2 — Co-creación en desarrollo guiado por guías

#### Herramientas utilizadas
- Claude
- ChatGPT

#### Uso de IA

Se utilizó Claude como apoyo para estructurar el ejercicio de IA 2 y organizar los artefactos solicitados por el reto, especialmente en:

- separación del entregable entre `RESPUESTAS.md` y la carpeta `specs/`;
- definición de la estructura de `requirements.md`, `design.md`, `plan.md`, `rules.md` y `bitacora.md`;
- organización de las 15 respuestas del reto por los bloques A, B, C y D;
- apoyo para convertir experiencias reales de la prueba en ejemplos concretos;
- identificación de decisiones, correcciones y rechazos realizados durante el desarrollo;
- definición de criterios de aceptación verificables;
- descomposición de la funcionalidad seleccionada en unidades de trabajo;
- trazabilidad entre criterios de aceptación y unidades de trabajo;
- documentación de alternativas descartadas y su justificación;
- preparación de una guía de reglas para el asistente;
- documentación de una bitácora de aprobación, corrección y rechazo de propuestas de IA.

Se utilizó ChatGPT para:

- revisar el documento de la prueba de IA y diferenciar claramente IA 1 de IA 2;
- confirmar que IA 2 era obligatorio e independiente de IA 1;
- interpretar el objetivo de desarrollo guiado por guías, AI-DLC y Spec-Driven Development;
- revisar el requisito de respuestas de 150 a 300 palabras y la necesidad de utilizar ejemplos reales;
- seleccionar la carga masiva de asociados del Backend 4 como funcionalidad para el ejercicio práctico;
- convertir la experiencia real de desarrollo de Backend 4 y DevOps en ejemplos para las respuestas;
- estructurar las respuestas evitando definiciones genéricas;
- definir criterios de aceptación en formato verificable;
- separar requisitos funcionales, decisiones de diseño y plan de implementación;
- dividir la carga masiva de asociados en unidades de trabajo pequeñas y dimensionadas;
- relacionar las unidades de trabajo con los criterios de aceptación;
- definir reglas explícitas para el uso de asistentes de IA;
- construir una bitácora coherente con las decisiones tomadas durante la implementación;
- revisar la nota del documento sobre commits y aclarar que solo aplica a nueva implementación realizada dentro del ejercicio;
- verificar que no fuera necesario modificar retroactivamente el historial de Git de la funcionalidad ya implementada.

#### Decisiones y validaciones propias

- Se decidió utilizar como ejercicio práctico la funcionalidad de carga masiva de asociados ya implementada en Backend 4.
- Se evitó crear una funcionalidad nueva únicamente para cumplir IA 2.
- Se decidió documentar el proceso de forma retrospectiva pero coherente con las decisiones reales tomadas durante el desarrollo.
- Se mantuvieron ejemplos basados en situaciones reales ocurridas durante Backend y DevOps, en lugar de utilizar ejemplos abstractos.
- Se decidió que los criterios de aceptación utilizaran identificadores estables como `AC-01`, `AC-02`, etc.
- Se organizó `plan.md` utilizando unidades de trabajo `UT-01`, `UT-02`, etc., dimensionadas como XS, S o M.
- Se relacionaron explícitamente las unidades de trabajo con uno o más criterios de aceptación.
- Se decidió separar parsing, normalización, validación y persistencia en la carga masiva para reducir acoplamiento.
- Se mantuvo la decisión de procesar filas de forma independiente para que una fila inválida no invalide las filas correctas.
- Se rechazó como diseño principal una transacción global que abortara toda la carga ante el primer error.
- Se mantuvo la reutilización de las reglas de negocio existentes para evitar duplicar validaciones entre el flujo individual y el flujo masivo.
- Se decidió utilizar identificadores funcionales como email o identificación en lugar de depender de IDs internos.
- Se documentaron como reglas del asistente la prohibición de hardcodear secretos, ejecutar comandos destructivos sin aprobación o introducir dependencias sin justificación.
- Se mantuvo la aprobación humana como requisito para decisiones que afecten seguridad, contratos, persistencia, permisos o arquitectura.
- Se utilizaron experiencias reales de esta misma prueba para justificar la importancia de validar las propuestas de IA contra el entorno real.
- Se documentó en la bitácora cuándo una propuesta de IA fue aceptada, rechazada o corregida y el motivo de la decisión.
- Se decidió no reescribir ni alterar commits antiguos de Backend 4 para agregar referencias `UT-*`, ya que la funcionalidad ya estaba implementada antes del ejercicio de IA 2.
- Se dejó establecido que, si se realizara nueva implementación dentro de IA 2, los nuevos commits sí deberían referenciar las unidades correspondientes de `plan.md`.
