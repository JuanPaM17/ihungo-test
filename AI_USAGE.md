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

### Backend 4

## DevOps
### DevOps 1
### DevOps 2
### DevOps 3

## IA
### IA 1
### IA 2