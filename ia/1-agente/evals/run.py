"""
evals/run.py — Runner de evaluaciones del agente ihungo V2.

Invoca process_query_v2 directamente (sin HTTP) con el provider real
configurado en ENV. Mockea el backend para evitar escrituras reales.

Uso:
    python evals/run.py
    python evals/run.py --category ambiguity
    python evals/run.py --case injection_01
    python evals/run.py --no-mock-reads   # usa backend real para lecturas

Variables de entorno requeridas:
    OPENAI_API_KEY (o GEMINI_API_KEY según MODEL_PROVIDER)
    EVAL_TOKEN        JWT fake o real para propagar a las tools
    API_ENDPOINT      Backend 4 (solo si --no-mock-reads)

Variables opcionales:
    EVAL_MOCK_WRITES=true   (default true)  — nunca escribe en backend real
    EVAL_MOCK_READS=true    (default true)  — usa fixtures para lecturas
"""

import asyncio
import argparse
import json
import os
import sys
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, patch

import yaml
from dotenv import load_dotenv

load_dotenv()

# Asegurar que evals/ esté en el path para imports relativos
sys.path.insert(0, str(Path(__file__).parent))

# ── Paths ─────────────────────────────────────────────────────────────────────
EVALS_DIR = Path(__file__).parent
CASOS_PATH = EVALS_DIR / "casos.yaml"
RESULTS_DIR = EVALS_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ── Config ────────────────────────────────────────────────────────────────────
TENANT_ID = "ihungo"
EVAL_TOKEN = os.getenv("EVAL_TOKEN", "eval-fake-token")
MOCK_WRITES = os.getenv("EVAL_MOCK_WRITES", "true").lower() == "true"
MOCK_READS = os.getenv("EVAL_MOCK_READS", "true").lower() == "true"


# ── Colores para consola ──────────────────────────────────────────────────────
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
RESET = "\033[0m"

PASS_ICON = "[PASS]"
FAIL_ICON = "[FAIL]"


def _check_env():
    provider = os.getenv("MODEL_PROVIDER", "openai").lower()
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        print(f"{RED}ERROR: OPENAI_API_KEY not set. Export it before running evals.{RESET}")
        sys.exit(1)
    if provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
        print(f"{RED}ERROR: GEMINI_API_KEY not set. Export it before running evals.{RESET}")
        sys.exit(1)


def _load_cases(category: Optional[str] = None, case_id: Optional[str] = None) -> list:
    with open(CASOS_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    cases = data["cases"]
    if case_id:
        cases = [c for c in cases if c["id"] == case_id]
        if not cases:
            print(f"{RED}Case '{case_id}' not found in casos.yaml{RESET}")
            sys.exit(1)
    if category:
        cases = [c for c in cases if c["category"] == category]
        if not cases:
            print(f"{RED}No cases found for category '{category}'{RESET}")
            sys.exit(1)
    return cases


async def _run_turn(
    query: str,
    thread_id: str,
    process_query_v2,
    main_graph,
    turn_start_index: int,
) -> tuple[str, list]:
    """
    Ejecuta un turno y devuelve (respuesta_final, mensajes_del_turno).
    """
    from graphs.utils import innermost_subgraph_state
    from langchain_core.runnables import RunnableConfig

    response = await process_query_v2(
        tenant_id=TENANT_ID,
        query=query,
        thread_id=thread_id,
        token=EVAL_TOKEN,
        document="_None_",
        user_name="eval_user",
        is_anonymous=False,
        language="es",
        version="v2",
    )

    # Capturar mensajes del turno desde el estado final
    configuration = RunnableConfig(
        configurable={
            "tenant_id": TENANT_ID,
            "thread_id": thread_id,
            "version": "v2",
            "token": EVAL_TOKEN,
        }
    )
    snap = await main_graph.aget_state(configuration, subgraphs=True)
    fs = innermost_subgraph_state(snap)
    all_messages = fs.values.get("messages", []) if fs else []
    turn_messages = all_messages[turn_start_index:]

    return response, turn_messages, len(all_messages)


async def _run_case(case: dict, process_query_v2, get_graph) -> dict:
    """Ejecuta todos los turnos de un caso y devuelve el resultado."""
    from evals.evaluator import evaluate_criteria

    case_id = case["id"]
    thread_id = str(uuid.uuid4())
    turns = case["turns"]

    turn_results = []
    case_passed = True
    current_msg_index = 0

    # Obtener el grafo una vez por caso (mismo thread_id = mismo grafo cacheado)
    main_graph = await get_graph(thread_id)

    for i, turn in enumerate(turns):
        query = turn["user"]
        criteria = turn.get("criteria", [])

        t0 = time.monotonic()
        try:
            response, turn_messages, new_index = await _run_turn(
                query=query,
                thread_id=thread_id,
                process_query_v2=process_query_v2,
                main_graph=main_graph,
                turn_start_index=current_msg_index,
            )
            current_msg_index = new_index
            latency_ms = int((time.monotonic() - t0) * 1000)

            criteria_results = evaluate_criteria(criteria, turn_messages, response)
            turn_passed = all(r["passed"] for r in criteria_results)

        except Exception as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            response = f"ERROR: {type(exc).__name__}: {exc}"
            criteria_results = [{"criterion": c, "passed": False, "reason": str(exc)} for c in criteria]
            turn_passed = False

        if not turn_passed:
            case_passed = False

        turn_results.append({
            "turn": i + 1,
            "user": query,
            "response_preview": response[:120] if response else "",
            "latency_ms": latency_ms,
            "criteria": criteria_results,
            "passed": turn_passed,
        })

    return {
        "id": case_id,
        "category": case["category"],
        "description": case.get("description", ""),
        "passed": case_passed,
        "turns": turn_results,
    }


def _print_case_result(result: dict):
    icon = f"{GREEN}{PASS_ICON}{RESET}" if result["passed"] else f"{RED}{FAIL_ICON}{RESET}"
    print(f"  {icon} [{result['category']}] {result['id']} - {result['description']}")
    if not result["passed"]:
        for turn in result["turns"]:
            for cr in turn["criteria"]:
                if not cr["passed"]:
                    print(f"      {RED}  turn {turn['turn']} | {cr['criterion']}: {cr['reason']}{RESET}")
                    print(f"        response: {turn['response_preview']!r}")


def _print_report(results: list, elapsed: float):
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    accuracy = (passed / total * 100) if total > 0 else 0

    # Por categoría
    by_cat: dict[str, dict] = {}
    for r in results:
        cat = r["category"]
        by_cat.setdefault(cat, {"total": 0, "passed": 0})
        by_cat[cat]["total"] += 1
        if r["passed"]:
            by_cat[cat]["passed"] += 1

    print(f"\n{BOLD}{'-'*55}{RESET}")
    print(f"{BOLD}EVAL REPORT -- ihungo V2{RESET}")
    print(f"{'-'*55}")
    print(f"  Provider : {os.getenv('MODEL_PROVIDER', 'openai').upper()}")
    print(f"  Model    : {os.getenv('OPENAI_MODEL') or os.getenv('GEMINI_MODEL', 'unknown')}")
    print(f"  Elapsed  : {elapsed:.1f}s")
    print(f"{'-'*55}")
    print(f"  Total    : {total}")
    print(f"  {GREEN}Passed   : {passed}{RESET}")
    print(f"  {RED}Failed   : {failed}{RESET}")
    print(f"  Accuracy : {BOLD}{accuracy:.2f}%{RESET}")
    print(f"{'-'*55}")
    print(f"{BOLD}By category:{RESET}")
    for cat, stats in sorted(by_cat.items()):
        cat_acc = stats["passed"] / stats["total"] * 100
        color = GREEN if cat_acc == 100 else (YELLOW if cat_acc >= 50 else RED)
        print(f"  {cat:<20} {color}{stats['passed']}/{stats['total']} ({cat_acc:.0f}%){RESET}")

    failed_cases = [r for r in results if not r["passed"]]
    if failed_cases:
        print(f"\n{RED}{BOLD}FAILED:{RESET}")
        for r in failed_cases:
            print(f"  - {r['id']}")
            for turn in r["turns"]:
                for cr in turn["criteria"]:
                    if not cr["passed"]:
                        print(f"      turn {turn['turn']} | {cr['criterion']}: {cr['reason']}")
    else:
        print(f"\n{GREEN}{BOLD}All cases passed!{RESET}")

    print(f"{'-'*55}\n")


def _save_results(results: list, elapsed: float):
    from zoneinfo import ZoneInfo
    now = datetime.now(tz=ZoneInfo("America/Bogota"))
    offset = now.strftime("%z")
    utc_offset = f"{offset[:3]}:{offset[3:]}"
    timestamp = now.strftime(f"%Y-%m-%dT%H:%M:%S{utc_offset}")

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    by_cat: dict = {}
    for r in results:
        cat = r["category"]
        by_cat.setdefault(cat, {"total": 0, "passed": 0})
        by_cat[cat]["total"] += 1
        if r["passed"]:
            by_cat[cat]["passed"] += 1

    report = {
        "timestamp": timestamp,
        "provider": os.getenv("MODEL_PROVIDER", "openai"),
        "model": os.getenv("OPENAI_MODEL") or os.getenv("GEMINI_MODEL", "unknown"),
        "elapsed_s": round(elapsed, 2),
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "accuracy": round(passed / total * 100, 2) if total > 0 else 0,
        "by_category": {
            cat: {
                "passed": v["passed"],
                "total": v["total"],
                "accuracy": round(v["passed"] / v["total"] * 100, 2),
            }
            for cat, v in by_cat.items()
        },
        "results": results,
    }

    out_path = RESULTS_DIR / "latest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  Results saved -> {out_path}")


async def main(category: Optional[str], case_id: Optional[str]):
    _check_env()

    from fixtures import mock_make_request  # noqa: E402 (relative to evals/)
    from version.assistant_v2 import process_query_v2, assistant_manager
    from graphs.utils import innermost_subgraph_state
    from langchain_core.runnables import RunnableConfig

    cases = _load_cases(category, case_id)

    print(f"\n{BOLD}Running {len(cases)} eval case(s)...{RESET}")
    print(f"  Mock writes : {MOCK_WRITES}")
    print(f"  Mock reads  : {MOCK_READS}\n")

    async def get_graph(thread_id: str):
        """Obtiene el grafo cacheado para el tenant (lo construye si no existe)."""
        user_state = {"is_anonymous": False, "user_name": "eval_user"}
        return await assistant_manager.get_graph_for_tenant(TENANT_ID, "v2", user_state)

    results = []
    t_start = time.monotonic()

    # Aplicar mock del backend según configuración
    should_mock = MOCK_WRITES or MOCK_READS

    async def selective_mock(method, endpoint, **kwargs):
        from utils.request import HTTPMethod
        is_write = method in (HTTPMethod.POST, HTTPMethod.PATCH, HTTPMethod.PUT, HTTPMethod.DELETE)
        if (is_write and MOCK_WRITES) or (not is_write and MOCK_READS):
            return await mock_make_request(method, endpoint, **kwargs)
        # Llamada real al backend
        raise RuntimeError("Real backend call attempted but mocking is active")

    mock_target = "utils.request.ApiRequestManager.make_request"

    for case in cases:
        print(f"  {CYAN}>> {case['id']}{RESET}", end=" ", flush=True)

        # Limpiar caché de tools para cada caso
        for tool_cls_name in ["ActividadTool", "AsociadoTool", "SystemTool"]:
            try:
                mod_map = {
                    "ActividadTool": "tools.actividades.actividades_tool",
                    "AsociadoTool": "tools.asociados.asociados_tool",
                    "SystemTool": "tools.system.system",
                }
                import importlib
                mod = importlib.import_module(mod_map[tool_cls_name])
                cls = getattr(mod, tool_cls_name)
                cls._configs = {}
            except Exception:
                pass

        if should_mock:
            with patch(mock_target, new=AsyncMock(side_effect=selective_mock)):
                result = await _run_case(case, process_query_v2, get_graph)
        else:
            result = await _run_case(case, process_query_v2, get_graph)

        results.append(result)
        icon = f"{GREEN}{PASS_ICON}{RESET}" if result["passed"] else f"{RED}{FAIL_ICON}{RESET}"
        print(icon)
        if not result["passed"]:
            _print_case_result(result)

    elapsed = time.monotonic() - t_start
    _print_report(results, elapsed)
    _save_results(results, elapsed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ihungo agent eval runner")
    parser.add_argument("--category", type=str, help="Run only cases of this category")
    parser.add_argument("--case", type=str, help="Run only this specific case id")
    parser.add_argument(
        "--no-mock-reads",
        action="store_true",
        help="Use real backend for read operations (requires API_ENDPOINT + EVAL_TOKEN)",
    )
    args = parser.parse_args()

    if args.no_mock_reads:
        os.environ["EVAL_MOCK_READS"] = "false"

    asyncio.run(main(category=args.category, case_id=args.case))
