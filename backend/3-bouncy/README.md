# Backend 3 — Bouncy Numbers

Un número es **increasing** si ningún dígito es menor que el anterior (ej: 134468).
Un número es **decreasing** si ningún dígito es mayor que el anterior (ej: 66420).
Un número es **bouncy** si no es ni increasing ni decreasing (ej: 155349).

El objetivo es encontrar el menor número para el cual la proporción de bouncy numbers sea exactamente un porcentaje dado.

---

## Python

### Instalación

```bash
cd python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Ejecutar tests

```bash
pytest test_bouncy.py -v
```

### Ejecutar CLI

```bash
python bouncy.py 99
```

---

## TypeScript

### Instalar dependencias

```bash
cd typescript
npm install
```

### Ejecutar CLI

```bash
npm run cli 99
```

### Ejecutar tests

```bash
npm test
```

---

## Casos verificados

| Porcentaje | Resultado |
|---|---|
| 50% | 538 |
| 90% | 21780 |
| 99% | 1587000 |

---

## Complejidad

| | Valor |
|---|---|
| **Temporal** | O(n · d) donde n es el número resultado y d la cantidad de dígitos por número (d ≤ 7 para 99%). Prácticamente O(n). |
| **Espacial** | O(d) — solo se almacenan los dígitos del número actual. |

---

## Tiempo de ejecución para 99%

| Lenguaje | Tiempo aproximado |
|---|---|
| Python | ~3–5 segundos |
| TypeScript | ~0.5–1 segundo |

> Medido en hardware estándar. Para medir en tu máquina:
>
> ```bash
> # Python
> time python bouncy.py 99
>
> # TypeScript
> time npm run cli 99
> ```
