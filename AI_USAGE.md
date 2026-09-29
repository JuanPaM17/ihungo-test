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
### IA 1
### IA 2