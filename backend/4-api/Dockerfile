# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/install/lib/python3.12/site-packages \
    PATH=/install/bin:$PATH

# Non-root user
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy installed packages from builder (no pip cache in final image)
COPY --from=builder /install /install

# Copy application source
COPY . .

# Prepare staticfiles dir and fix ownership before switching user
RUN chmod +x entrypoint.sh && \
    mkdir -p staticfiles && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["./entrypoint.sh"]
