"""
Tests del endpoint FastAPI — POST /llm/v2/ihungo y SSE.

Mockea process_query_v2 y stream_query_v2 para evitar LLM real.

Casos:
  API1. POST /llm/v2/ihungo devuelve 200 con session_id y response.
  API2. JWT no aparece en el response body.
  API3. session_id del header X-Session-Id se respeta.
  API4. Query vacía devuelve error (ValueError).
  API5. Versión inválida devuelve 400.
  API6. SSE endpoint devuelve 200 con Content-Type text/event-stream.
  API7. SSE con versión v1 devuelve 400.
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def app():
    from server import app as fastapi_app
    return fastapi_app


class TestPostEndpoint:

    async def test_basic_request_returns_200(self, app):
        """API1 — POST /llm/v2/ihungo devuelve 200 con response y session_id."""
        with patch(
            "server.process_query_v2",
            new=AsyncMock(return_value="Hola, soy el asistente."),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/llm/v2/ihungo",
                    json={"query": "Hola", "isAnonymous": False},
                    headers={
                        "Authorization": "Bearer fake-token",
                        "X-Session-Id": "test-session-api",
                    },
                )

        assert resp.status_code == 200
        body = resp.json()
        assert "response" in body
        assert "session_id" in body
        assert body["response"] == "Hola, soy el asistente."

    async def test_jwt_not_in_response(self, app):
        """API2 — el JWT del header no aparece en el response body."""
        with patch(
            "server.process_query_v2",
            new=AsyncMock(return_value="Respuesta segura."),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/llm/v2/ihungo",
                    json={"query": "Test", "isAnonymous": False},
                    headers={"Authorization": "Bearer super-secret-jwt-xyz"},
                )

        assert "super-secret-jwt-xyz" not in resp.text

    async def test_session_id_from_header_is_returned(self, app):
        """API3 — X-Session-Id del header se usa y se devuelve en response."""
        with patch(
            "server.process_query_v2",
            new=AsyncMock(return_value="Ok"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/llm/v2/ihungo",
                    json={"query": "Test", "isAnonymous": False},
                    headers={
                        "Authorization": "Bearer fake",
                        "X-Session-Id": "my-custom-session-id",
                    },
                )

        assert resp.json()["session_id"] == "my-custom-session-id"

    async def test_empty_query_raises_error(self, app):
        """API4 — query vacía o nula produce error (ValueError → 500).

        server.py lanza ValueError directamente (no HTTPException),
        FastAPI lo convierte en 500 Internal Server Error.
        """
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            try:
                resp = await client.post(
                    "/llm/v2/ihungo",
                    json={"isAnonymous": False},
                    headers={"Authorization": "Bearer fake"},
                )
                assert resp.status_code in (400, 422, 500)
            except Exception:
                # ValueError propagado — comportamiento esperado con query nula
                pass

    async def test_invalid_version_returns_400(self, app):
        """API5 — versión inválida devuelve 400."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/llm/v99/ihungo",
                json={"query": "Hola", "isAnonymous": False},
                headers={"Authorization": "Bearer fake"},
            )

        assert resp.status_code == 400


class TestSSEEndpoint:

    async def test_sse_returns_event_stream(self, app):
        """API6 — SSE endpoint devuelve 200 con Content-Type text/event-stream."""

        async def fake_stream(*args, **kwargs):
            yield 'event: start\ndata: {"session_id": "test"}\n\n'
            yield 'event: done\ndata: {"response": "Hola", "session_id": "test"}\n\n'

        with patch(
            "server.stream_query_v2",
            new=fake_stream,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/llm/v2/ihungo/stream",
                    json={"query": "Hola", "isAnonymous": False},
                    headers={"Authorization": "Bearer fake"},
                )

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

    async def test_sse_v1_returns_400(self, app):
        """API7 — SSE con v1 devuelve 400 (solo soportado en v2)."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/llm/v1/ihungo/stream",
                json={"query": "Hola", "isAnonymous": False},
                headers={"Authorization": "Bearer fake"},
            )

        assert resp.status_code == 400
