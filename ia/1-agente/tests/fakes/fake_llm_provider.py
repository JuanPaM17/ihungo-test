"""
FakeLLMProvider — implementa la misma interfaz que LLMProvider.

Devuelve un FakeListChatModel de langchain_core que consume respuestas
scripted en orden. No hace llamadas externas.

Uso:
    from tests.fakes.fake_llm_provider import FakeLLMProvider

    provider = FakeLLMProvider(responses=["Hola, soy el asistente."])
    llms = provider.build_available_llms()
    # llms["default"], llms["fast"], llms["evaluator"] son el mismo FakeListChatModel
"""

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.language_models.chat_models import BaseChatModel


class FakeLLMProvider:
    """
    Provider de pruebas. Implementa la misma interfaz que OpenAIProvider/GeminiProvider.

    Args:
        responses: lista de strings que el modelo devolverá en orden.
                   Si se agotan, devuelve el último indefinidamente.
    """

    def __init__(self, responses: list[str] | None = None):
        self._responses = responses or ["Respuesta de prueba del agente."]

    def get_model(self, alias: str) -> BaseChatModel:
        # FakeListChatModel cicla desde el inicio cuando se agota la lista
        return FakeListChatModel(responses=self._responses)

    def build_available_llms(self) -> dict:
        """Devuelve el mismo fake para default, fast y evaluator."""
        model = self.get_model("default")
        return {
            "default": model,
            "fast": model,
            "evaluator": model,
        }
