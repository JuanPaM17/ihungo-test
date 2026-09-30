"""
LLM Provider abstraction.

Selects the LLM backend via MODEL_PROVIDER env var (openai | gemini).
Returns LangChain-compatible BaseChatModel instances.

Usage:
    from utils.llm_provider import build_available_llms
    available_llms = build_available_llms()
    # Keys: "default", "fast", "evaluator"
"""
import os
import logging
from abc import ABC, abstractmethod
from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Base interface for LLM providers."""

    @abstractmethod
    def get_model(self, alias: str) -> BaseChatModel:
        """Return a LangChain-compatible chat model for the given alias."""


class OpenAIProvider(LLMProvider):
    """OpenAI provider via langchain-openai."""

    ALIAS_MAP = {
        "default":   os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "fast":      os.getenv("OPENAI_MODEL_FAST", "gpt-4.1-nano"),
        "evaluator": os.getenv("OPENAI_MODEL_EVALUATOR", "gpt-4.1-mini"),
    }

    def __init__(self):
        from langchain_openai import ChatOpenAI
        self._cls = ChatOpenAI
        self._api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        self._temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
        self._timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIProvider")

    def get_model(self, alias: str) -> BaseChatModel:
        model_name = self.ALIAS_MAP.get(alias, self.ALIAS_MAP["default"])
        logger.debug("OpenAIProvider: alias=%s model=%s", alias, model_name)
        return self._cls(
            model=model_name,
            api_key=self._api_key,
            temperature=self._temperature,
            timeout=self._timeout,
        )


class GeminiProvider(LLMProvider):
    """Google Gemini provider via langchain-google-genai."""

    ALIAS_MAP = {
        "default":   os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        "fast":      os.getenv("GEMINI_MODEL_FAST", "gemini-2.0-flash"),
        "evaluator": os.getenv("GEMINI_MODEL_EVALUATOR", "gemini-2.0-flash"),
    }

    def __init__(self):
        from langchain_google_genai import ChatGoogleGenerativeAI
        self._cls = ChatGoogleGenerativeAI
        self._api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
        self._temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
        self._timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiProvider")

    def get_model(self, alias: str) -> BaseChatModel:
        model_name = self.ALIAS_MAP.get(alias, self.ALIAS_MAP["default"])
        logger.debug("GeminiProvider: alias=%s model=%s", alias, model_name)
        return self._cls(
            model=model_name,
            google_api_key=self._api_key,
            temperature=self._temperature,
            timeout=self._timeout,
        )


def get_provider() -> LLMProvider:
    """Instantiate the provider selected by MODEL_PROVIDER env var."""
    provider_name = os.getenv("MODEL_PROVIDER", "openai").lower().strip()
    logger.info("LLMProvider: using provider=%s", provider_name)
    if provider_name == "openai":
        return OpenAIProvider()
    if provider_name == "gemini":
        return GeminiProvider()
    raise ValueError(
        f"Unsupported MODEL_PROVIDER='{provider_name}'. Valid values: openai, gemini"
    )


def build_available_llms() -> dict:
    """
    Build the available_llms dict consumed by V2 graph components.

    Returns:
        {
            "default":   BaseChatModel,
            "fast":      BaseChatModel,
            "evaluator": BaseChatModel,
        }
    """
    provider = get_provider()
    return {
        "default":   provider.get_model("default"),
        "fast":      provider.get_model("fast"),
        "evaluator": provider.get_model("evaluator"),
    }
