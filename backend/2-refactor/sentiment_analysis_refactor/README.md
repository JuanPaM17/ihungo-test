# Sentiment Analysis — Refactor

Lee un archivo Excel, analiza el sentimiento de cada celda de texto usando ParallelDots y escribe las columnas **NEGATIVO / NEUTRAL / POSITIVO** en un archivo de salida.

---

## Instalación

```bash
cd backend/2-refactor/sentiment_analysis_refactor

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / Mac

pip install -r requirements.txt
pip install -e .
```

---

## Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `PARALLELDOTS_API_KEY` | Sí | Tu API key de ParallelDots |

Copia `.env.example` a `.env` y completa el valor. Luego cárgala antes de ejecutar:

```bash
set PARALLELDOTS_API_KEY=tu_api_key      # Windows cmd
# export PARALLELDOTS_API_KEY=tu_api_key # bash / Mac
```

---

## Cómo ejecutar

```bash
sentiment-analysis --input archivo.xlsx --output resultado.xlsx
```

- `--input` es el Excel que **vas a leer** (tu archivo original, no se modifica).
- `--output` es el Excel que **se genera** con las columnas de sentimiento agregadas.

### Todos los argumentos

```bash
sentiment-analysis \
  --input  archivo.xlsx \
  --output resultado.xlsx \
  --sheet  "Hoja1" \
  --column 3
```

| Argumento | Por defecto | Descripción |
|---|---|---|
| `--input` | — | Ruta al Excel de entrada |
| `--output` | — | Ruta del Excel de salida |
| `--sheet` | hoja activa | Nombre de la hoja a procesar |
| `--column` | `3` | Número de columna (base 1) que contiene el texto |

### Ejemplo

Si tu texto está en la columna B (columna 2):

```bash
sentiment-analysis --input ventas.xlsx --output ventas_resultado.xlsx --column 2
```

---

## Tests

```bash
pytest
```

### Cobertura

```bash
pytest --cov=sentiment_analysis --cov-report=term-missing
```

---

## Lint y tipos

```bash
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/
```

---

## Estructura del proyecto

```
sentiment_analysis_refactor/
├── .env.example
├── pyproject.toml
├── requirements.txt
├── README.md
├── src/
│   └── sentiment_analysis/
│       ├── __init__.py
│       ├── cli.py
│       ├── models.py
│       ├── processor.py
│       └── providers/
│           ├── __init__.py
│           ├── base.py
│           └── paralleldots.py
└── tests/
    ├── __init__.py
    ├── fakes.py
    ├── test_processor.py
    └── test_cli.py
```
