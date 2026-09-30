"""
Tests de tools: list_actividades, buscar_asociados, consultar_disponibilidad.
Mockea ApiRequestManager.make_request — sin llamadas HTTP reales.

Casos cubiertos:
  A. listar_actividades — ok, vacío, error backend
  B. buscar_asociados   — 1 coincidencia, múltiples, ninguna, sin filtros
  C. consultar_disponibilidad — libre, ocupado, múltiples asociados
  D. create_actividad   — timeout backend
  E. update/delete      — 404 backend
"""

import pytest
from unittest.mock import AsyncMock, patch

from tests.fakes.fake_backend import (
    ACTIVIDADES_SAMPLE,
    ASOCIADOS_SAMPLE,
    DISPONIBILIDAD_SAMPLE,
    ACTIVIDAD_CREATED,
    ACTIVIDAD_UPDATED,
    ok_actividades,
    empty_actividades,
    error_actividades,
    ok_asociados_all,
    ok_asociados_one,
    empty_asociados,
    ok_disponibilidad,
    ok_create,
    ok_update,
    ok_delete,
    error_404,
    error_500,
    raise_timeout,
)


# ── A. listar_actividades ──────────────────────────────────────────────────────

class TestListActividades:

    async def test_returns_actividades(self, fake_config):
        """A1 — backend devuelve actividades correctamente."""
        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=ok_actividades),
        ):
            # Reset cache so tenant config uses mocked manager
            from tools.actividades.actividades_tool import ActividadTool
            ActividadTool._configs = {}

            from tools.actividades.actividades_tool import list_actividades
            result = await list_actividades.ainvoke({}, config=fake_config)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == 1

    async def test_returns_empty(self, fake_config):
        """A2 — backend responde vacío."""
        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=empty_actividades),
        ):
            from tools.actividades.actividades_tool import ActividadTool
            ActividadTool._configs = {}

            from tools.actividades.actividades_tool import list_actividades
            result = await list_actividades.ainvoke({}, config=fake_config)

        assert result == []

    async def test_backend_error(self, fake_config):
        """A3 — backend responde error 500."""
        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=error_actividades),
        ):
            from tools.actividades.actividades_tool import ActividadTool
            ActividadTool._configs = {}

            from tools.actividades.actividades_tool import list_actividades
            result = await list_actividades.ainvoke({}, config=fake_config)

        assert isinstance(result, dict)
        assert "error" in result


# ── B. buscar_asociados ────────────────────────────────────────────────────────

class TestBuscarAsociados:

    async def test_una_coincidencia(self, fake_config):
        """B1 — una coincidencia."""
        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=ok_asociados_one),
        ):
            from tools.asociados.asociados_tool import AsociadoTool
            AsociadoTool._configs = {}

            from tools.asociados.asociados_tool import buscar_asociados
            result = await buscar_asociados.ainvoke({"nombre": "Juan"}, config=fake_config)

        assert result["total"] == 1
        assert "1 asociado" in result["mensaje"]
        assert result["coincidencias"][0]["first_name"] == "Juan"

    async def test_multiples_coincidencias(self, fake_config):
        """B2 — múltiples coincidencias."""
        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=ok_asociados_all),
        ):
            from tools.asociados.asociados_tool import AsociadoTool
            AsociadoTool._configs = {}

            from tools.asociados.asociados_tool import buscar_asociados
            result = await buscar_asociados.ainvoke({"ciudad": "Bogotá"}, config=fake_config)

        assert result["total"] == 2
        assert "2 asociados" in result["mensaje"]

    async def test_ninguna_coincidencia(self, fake_config):
        """B3 — ninguna coincidencia."""
        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=empty_asociados),
        ):
            from tools.asociados.asociados_tool import AsociadoTool
            AsociadoTool._configs = {}

            from tools.asociados.asociados_tool import buscar_asociados
            result = await buscar_asociados.ainvoke({"nombre": "XYZNoExiste"}, config=fake_config)

        assert result["total"] == 0
        assert "No se encontraron" in result["mensaje"]

    async def test_sin_filtros_no_llama_backend(self, fake_config):
        """B4 — sin filtros retorna error inmediato sin llamar backend."""
        mock = AsyncMock(side_effect=ok_asociados_all)
        with patch("utils.request.ApiRequestManager.make_request", new=mock):
            from tools.asociados.asociados_tool import AsociadoTool
            AsociadoTool._configs = {}

            from tools.asociados.asociados_tool import buscar_asociados
            result = await buscar_asociados.ainvoke({}, config=fake_config)

        assert result["total"] == 0
        assert "filtro" in result["mensaje"].lower()
        mock.assert_not_called()


# ── C. consultar_disponibilidad ────────────────────────────────────────────────

class TestConsultarDisponibilidad:

    async def test_disponibilidad_ok(self, fake_config):
        """C1 — respuesta con libre y ocupado."""
        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=ok_disponibilidad),
        ):
            from tools.actividades.actividades_tool import ActividadTool
            ActividadTool._configs = {}

            from tools.actividades.actividades_tool import consultar_disponibilidad
            result = await consultar_disponibilidad.ainvoke(
                {
                    "fecha_inicio": "2026-10-01T09:00:00-05:00",
                    "fecha_fin": "2026-10-01T11:00:00-05:00",
                },
                config=fake_config,
            )

        assert "asociados" in result
        assert result["resumen"]["libres"] == 1
        assert result["resumen"]["ocupados"] == 1

    async def test_asociado_libre(self, fake_config):
        """C2 — asociado 2 está libre."""
        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=ok_disponibilidad),
        ):
            from tools.actividades.actividades_tool import ActividadTool
            ActividadTool._configs = {}

            from tools.actividades.actividades_tool import consultar_disponibilidad
            result = await consultar_disponibilidad.ainvoke(
                {
                    "fecha_inicio": "2026-10-01T09:00:00-05:00",
                    "fecha_fin": "2026-10-01T11:00:00-05:00",
                    "asociado_id": 2,
                },
                config=fake_config,
            )

        libres = [a for a in result["asociados"] if a["estado"] == "libre"]
        assert any(a["id"] == 2 for a in libres)

    async def test_asociado_ocupado(self, fake_config):
        """C3 — asociado 1 está ocupado."""
        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=ok_disponibilidad),
        ):
            from tools.actividades.actividades_tool import ActividadTool
            ActividadTool._configs = {}

            from tools.actividades.actividades_tool import consultar_disponibilidad
            result = await consultar_disponibilidad.ainvoke(
                {
                    "fecha_inicio": "2026-10-01T09:00:00-05:00",
                    "fecha_fin": "2026-10-01T11:00:00-05:00",
                    "asociado_id": 1,
                },
                config=fake_config,
            )

        ocupados = [a for a in result["asociados"] if a["estado"] == "ocupado"]
        assert any(a["id"] == 1 for a in ocupados)


# ── D/E/F. create / update / delete — backend responses ───────────────────────

class TestWriteOperations:

    async def test_create_actividad_ok(self, fake_config):
        """D1 — create devuelve la actividad creada."""
        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=ok_create),
        ):
            from tools.actividades.actividades_tool import ActividadTool
            ActividadTool._configs = {}

            from tools.actividades.actividades_tool import create_actividad
            result = await create_actividad.ainvoke(
                {
                    "activity_type": "seminar",
                    "start_datetime": "2026-10-05T10:00:00-05:00",
                    "end_datetime": "2026-10-05T12:00:00-05:00",
                    "asociado": 1,
                },
                config=fake_config,
            )

        assert result["id"] == 99
        assert result["activity_type"] == "seminar"

    async def test_update_actividad_404(self, fake_config):
        """E1 — update con actividad inexistente devuelve error."""
        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=error_404),
        ):
            from tools.actividades.actividades_tool import ActividadTool
            ActividadTool._configs = {}

            from tools.actividades.actividades_tool import update_actividad
            result = await update_actividad.ainvoke(
                {
                    "actividad_id": 9999,
                    "description": "Nueva descripción",
                },
                config=fake_config,
            )

        assert "error" in result

    async def test_delete_actividad_ok(self, fake_config):
        """F1 — delete exitoso devuelve dict vacío o sin error."""
        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=ok_delete),
        ):
            from tools.actividades.actividades_tool import ActividadTool
            ActividadTool._configs = {}

            from tools.actividades.actividades_tool import delete_actividad
            result = await delete_actividad.ainvoke(
                {"actividad_id": 1},
                config=fake_config,
            )

        assert "error" not in result

    async def test_backend_timeout_create(self, fake_config):
        """L1 — timeout en create produce respuesta controlada (no crash).

        Simula el timeout devolviendo {"error": ...} directamente,
        replicando lo que ApiRequestManager hace al capturar ClientError.
        """
        async def timeout_as_error(*args, **kwargs):
            # Replica el comportamiento de ApiRequestManager al capturar aiohttp.ClientError
            return {"error": "ServerTimeoutError()"}

        with patch(
            "utils.request.ApiRequestManager.make_request",
            new=AsyncMock(side_effect=timeout_as_error),
        ):
            from tools.actividades.actividades_tool import ActividadTool
            ActividadTool._configs = {}

            from tools.actividades.actividades_tool import create_actividad
            result = await create_actividad.ainvoke(
                {
                    "activity_type": "seminar",
                    "start_datetime": "2026-10-05T10:00:00-05:00",
                    "end_datetime": "2026-10-05T12:00:00-05:00",
                    "asociado": 1,
                },
                config=fake_config,
            )

        assert isinstance(result, dict)
        assert "error" in result
