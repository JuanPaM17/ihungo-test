"""
conftest.py — fixtures compartidas para toda la suite de tests.

Garantiza que no se usen credenciales reales:
- OPENAI_API_KEY → "fake-key"
- GEMINI_API_KEY → "fake-key"
- LANGSMITH_TRACING → "false"
- API_ENDPOINT → "http://fake-backend"
"""

import os
import pytest

# ── Parchar env ANTES de que cualquier módulo del proyecto se importe ──────────
os.environ.setdefault("OPENAI_API_KEY", "fake-key")
os.environ.setdefault("GEMINI_API_KEY", "fake-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")
os.environ.setdefault("LANGSMITH_API_KEY", "fake-ls-key")
os.environ.setdefault("API_ENDPOINT", "http://fake-backend")
os.environ.setdefault("MODEL_PROVIDER", "openai")
os.environ.setdefault("OPENAI_MODEL", "gpt-4.1-mini")
os.environ.setdefault("TENANT_CONFIG_BASE_PATH", "config/v2/tenants")
os.environ.setdefault("DYNAMIC_AGENTS_CONFIG_PATH", "dynamic_agents_config.json")
os.environ.setdefault("PROMPTS_AGENTS_BASE_PATH", "prompts/agents")
os.environ.setdefault("PROMPTS_BASE_PATH", "prompts")
os.environ.setdefault("GENERAL_PROMPT_PATH", "config/v2/prompts/general_prompt.md")


@pytest.fixture
def fake_config():
    """RunnableConfig mínimo con tenant_id y token fake."""
    return {
        "configurable": {
            "tenant_id": "ihungo",
            "token": "fake-jwt-token",
            "thread_id": "test-thread-001",
            "version": "v2",
        }
    }


@pytest.fixture
def tenant_id():
    return "ihungo"


@pytest.fixture
def fake_token():
    return "fake-jwt-token"
