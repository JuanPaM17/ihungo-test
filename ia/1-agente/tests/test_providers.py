"""
Tests de providers — caso K.

K1. MODEL_PROVIDER inválido produce ValueError controlado.
K2. FakeProvider puede sustituir provider real sin cambiar lógica del agente.
K3. build_available_llms devuelve las 3 claves requeridas.
"""

import os
import pytest
from unittest.mock import patch

from tests.fakes.fake_llm_provider import FakeLLMProvider


class TestProviders:

    def test_invalid_provider_raises(self):
        """K1 — MODEL_PROVIDER inválido lanza ValueError."""
        with patch.dict(os.environ, {"MODEL_PROVIDER": "invalid_provider"}):
            from utils import llm_provider
            import importlib
            importlib.reload(llm_provider)
            with pytest.raises(ValueError, match="Unsupported MODEL_PROVIDER"):
                llm_provider.get_provider()

    def test_fake_provider_has_required_keys(self):
        """K2 — FakeProvider devuelve las 3 claves requeridas."""
        provider = FakeLLMProvider(responses=["test"])
        llms = provider.build_available_llms()
        assert "default" in llms
        assert "fast" in llms
        assert "evaluator" in llms

    def test_fake_provider_models_are_callable(self):
        """K3 — modelos del FakeProvider son BaseChatModel válidos."""
        from langchain_core.language_models.chat_models import BaseChatModel
        provider = FakeLLMProvider(responses=["ok"])
        llms = provider.build_available_llms()
        for key, model in llms.items():
            assert isinstance(model, BaseChatModel), f"{key} no es BaseChatModel"

    def test_fake_provider_no_external_calls(self):
        """K4 — FakeProvider no depende de OPENAI_API_KEY."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            # No debe lanzar aunque la key esté vacía
            provider = FakeLLMProvider(responses=["ok"])
            llms = provider.build_available_llms()
            assert llms["default"] is not None
