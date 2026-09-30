# =============================================================================
# Assistant-IA / llm — Dockerfile
# =============================================================================
FROM python:3.11-slim

LABEL maintainer="ihungo" \
      description="ihungo IA: servicio de agentes conversacionales con LangGraph"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependencias Python (capa cacheable)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY server.py __init__.py ./
COPY graphs/ graphs/
COPY subgraphs/ subgraphs/
COPY tools/ tools/
COPY utils/ utils/
COPY version/ version/

# Copiar configuración de tenants y prompts (necesaria en runtime)
COPY config/ config/

# Usuario no-root por seguridad
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/llm/docs')" || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
