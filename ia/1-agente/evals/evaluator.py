"""
evals/evaluator.py — criterios deterministas de evaluación por turno.

Evalúa cada criterio declarado en casos.yaml contra el estado real
del grafo después de procesar el turno.

NO usa LLM-as-judge. Todos los criterios son estructurales.
"""

import re
from langchain_core.messages import ToolMessage, AIMessage


# ── Patrones de confirmación y aclaración ────────────────────────────────────

_CONFIRMATION_PATTERNS = [
    r"¿confirm",
    r"confirm[ao]",
    r"¿deseas",
    r"¿quieres",
    r"¿procedo",
    r"¿ejecuto",
    r"¿está[s]? segur",
    r"¿lo creo",
    r"¿lo elimin",
    r"¿lo actualiz",
    r"antes de continuar",
    r"¿debo",
    r"para confirmar",
]

_CLARIFICATION_PATTERNS = [
    # Preguntas directas
    r"¿cuál",
    r"¿a cuál",
    r"¿con cuál",
    r"¿de cuál",
    r"¿cuántos",
    r"¿qué asociado",
    r"¿con qu[eé] asociado",
    r"¿a qu[eé] asociado",
    # Múltiples resultados
    r"varios",
    r"múltiples",
    r"encontré \d+",
    r"se encontraron \d+",
    r"hay \d+ asociados",
    r"existen \d+",
    r"dos asociados",
    r"tres asociados",
    # Solicitud de más info
    r"especifica",
    r"necesito.*detalles",
    r"necesito saber",
    r"necesito.*informaci[oó]n",
    r"por favor.*indica",
    r"por favor.*especifica",
    r"por favor.*dime",
    r"¿podrías aclarar",
    r"¿podrías especificar",
    r"¿podrías indicar",
    r"¿podrías decirme",
    r"proporciona",
    r"ind[ií]came",
    # Hora ambigua
    r"¿am\b",
    r"¿pm\b",
    r"am o pm",
    r"mañana o tarde",
    r"¿a qué hora exactamente",
    # Formato lista de preguntas (el agente enumera qué necesita)
    r"\?.*\n.*\?",
    r"1\.\s.*\?",
    r"1\.\s.*asociado",
]

_WRITE_TOOLS = {"create_actividad", "update_actividad", "delete_actividad"}


def _get_turn_messages(messages: list, turn_start: int) -> list:
    return messages[turn_start:] if turn_start < len(messages) else []


def _tools_called(turn_messages: list) -> list[str]:
    return [m.name for m in turn_messages if isinstance(m, ToolMessage) and m.name]


def _last_ai_response(turn_messages: list) -> str:
    for m in reversed(turn_messages):
        if isinstance(m, AIMessage) and m.content:
            return m.content.lower() if isinstance(m.content, str) else ""
    return ""


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def evaluate_criteria(criteria: list[str], turn_messages: list, final_response: str) -> list[dict]:
    """
    Evalúa la lista de criterios de un turno.

    Returns:
        Lista de {criterion, passed, reason}
    """
    results = []
    called = _tools_called(turn_messages)
    response_lower = final_response.lower() if final_response else ""

    for criterion in criteria:
        passed = False
        reason = ""

        if criterion.startswith("tool_called:"):
            tool = criterion.split(":", 1)[1]
            passed = tool in called
            reason = f"Tool '{tool}' {'found' if passed else 'NOT found'} in {called}"

        elif criterion.startswith("tool_not_called:"):
            tool = criterion.split(":", 1)[1]
            passed = tool not in called
            reason = f"Tool '{tool}' {'correctly absent' if passed else 'UNEXPECTEDLY called'}"

        elif criterion == "no_write":
            write_calls = [t for t in called if t in _WRITE_TOOLS]
            passed = len(write_calls) == 0
            reason = f"Write tools called: {write_calls}" if not passed else "No write tools called"

        elif criterion == "asked_confirmation":
            passed = _matches_any(response_lower, _CONFIRMATION_PATTERNS)
            reason = "Confirmation pattern found" if passed else "No confirmation pattern in response"

        elif criterion == "asked_clarification":
            passed = _matches_any(response_lower, _CLARIFICATION_PATTERNS)
            reason = "Clarification pattern found" if passed else "No clarification pattern in response"

        elif criterion == "responded_without_error":
            passed = bool(final_response) and "traceback" not in response_lower and "exception" not in response_lower
            reason = "Response present and no error" if passed else "Empty or error response"

        else:
            passed = False
            reason = f"Unknown criterion: {criterion}"

        results.append({"criterion": criterion, "passed": passed, "reason": reason})

    return results
