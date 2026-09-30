"""
FakeBackend — fixtures y helpers para mockear ApiRequestManager.make_request.

No hace llamadas HTTP reales. Cada fixture devuelve datos de prueba
predefinidos que replican la forma real del backend Django.
"""

import asyncio

# ── Datos de prueba ────────────────────────────────────────────────────────────

ACTIVIDADES_SAMPLE = [
    {
        "id": 1,
        "activity_type": "workshop",
        "description": "Taller de liderazgo",
        "start_datetime": "2026-10-01T09:00:00-05:00",
        "end_datetime": "2026-10-01T11:00:00-05:00",
        "asociado": 1,
        "created_by": 1,
    },
    {
        "id": 2,
        "activity_type": "meeting",
        "description": "Reunión de seguimiento",
        "start_datetime": "2026-10-02T14:00:00-05:00",
        "end_datetime": "2026-10-02T15:00:00-05:00",
        "asociado": 2,
        "created_by": 1,
    },
]

ASOCIADOS_SAMPLE = [
    {
        "id": 1,
        "email": "juan.perez@example.com",
        "identification": "12345678",
        "first_name": "Juan",
        "last_name": "Pérez",
        "city": "Bogotá",
    },
    {
        "id": 2,
        "email": "maria.gomez@example.com",
        "identification": "87654321",
        "first_name": "María",
        "last_name": "Gómez",
        "city": "Medellín",
    },
]

DISPONIBILIDAD_SAMPLE = {
    "rango": {
        "inicio": "2026-10-01T09:00:00-05:00",
        "fin": "2026-10-01T11:00:00-05:00",
    },
    "resumen": {"libres": 1, "ocupados": 1},
    "asociados": [
        {
            "id": 1,
            "nombre": "Juan Pérez",
            "email": "juan.perez@example.com",
            "estado": "ocupado",
            "actividades_bloqueantes": [ACTIVIDADES_SAMPLE[0]],
        },
        {
            "id": 2,
            "nombre": "María Gómez",
            "email": "maria.gomez@example.com",
            "estado": "libre",
            "actividades_bloqueantes": [],
        },
    ],
}

ACTIVIDAD_CREATED = {
    "id": 99,
    "activity_type": "seminar",
    "description": "Seminario de prueba",
    "start_datetime": "2026-10-05T10:00:00-05:00",
    "end_datetime": "2026-10-05T12:00:00-05:00",
    "asociado": 1,
    "created_by": 1,
}

ACTIVIDAD_UPDATED = {**ACTIVIDAD_CREATED, "description": "Seminario actualizado"}


# ── Helpers para simular errores ───────────────────────────────────────────────

def backend_error(status: int, message: str = "") -> dict:
    return {"error": message or f"HTTP {status}"}


def backend_timeout() -> Exception:
    import aiohttp
    return aiohttp.ServerTimeoutError()


# ── AsyncMock factories ────────────────────────────────────────────────────────

async def ok_actividades(*args, **kwargs):
    return ACTIVIDADES_SAMPLE


async def empty_actividades(*args, **kwargs):
    return []


async def error_actividades(*args, **kwargs):
    return backend_error(500, "Internal server error")


async def ok_asociados_all(*args, **kwargs):
    return ASOCIADOS_SAMPLE


async def ok_asociados_one(*args, **kwargs):
    return [ASOCIADOS_SAMPLE[0]]


async def empty_asociados(*args, **kwargs):
    return []


async def ok_disponibilidad(*args, **kwargs):
    return DISPONIBILIDAD_SAMPLE


async def ok_create(*args, **kwargs):
    return ACTIVIDAD_CREATED


async def ok_update(*args, **kwargs):
    return ACTIVIDAD_UPDATED


async def ok_delete(*args, **kwargs):
    return {}


async def error_404(*args, **kwargs):
    return backend_error(404, "Not found")


async def error_401(*args, **kwargs):
    return backend_error(401, "Unauthorized")


async def error_500(*args, **kwargs):
    return backend_error(500, "Server error")


async def raise_timeout(*args, **kwargs):
    import aiohttp
    raise aiohttp.ServerTimeoutError()
