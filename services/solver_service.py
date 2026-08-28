from __future__ import annotations

from time import perf_counter
from typing import Any

from base_module import RationalNumber, rationalize
from main import EXAMPLES, Launcher


_STATUS_TO_SUBTYPE = {
    "LP": "two_phase",
    "IP": "branch_and_bound",
    "TP": "transportation",
    "AP": "hungarian",
    "GT": "game_theory",
}


def _rational(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        return RationalNumber.from_value(value).to_dict()
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _subtype(request: dict[str, Any], result: dict[str, Any]) -> str | None:
    if request.get("sub_type"):
        return request["sub_type"]
    if request.get("problem_type") == "LP":
        payload = request.get("payload") or {}
        return "graphical" if len(payload.get("c", [])) == 2 else "two_phase"
    return _STATUS_TO_SUBTYPE.get(request.get("problem_type"))


def normalize_result(request: dict[str, Any], result: dict[str, Any], elapsed_ms: float) -> dict[str, Any]:
    final = result.get("final_result") or {}
    options = request.get("options") or {}
    objective_sense = (request.get("payload") or {}).get("objective")
    value = final.get("objective_value", final.get("total_cost", final.get("game_value")))
    iterations = rationalize(result.get("iterations", []))
    diagnostics = {
        "elapsed_ms": round(elapsed_ms, 3),
        "total_steps": len(iterations),
        "degeneracy_detected": any(
            item.get("state_matrix", {}).get("b", []) and
            any(str(value) in {"0", "0/1"} for value in item["state_matrix"].get("b", []))
            for item in iterations
            if isinstance(item.get("state_matrix"), dict)
        ),
        "multiple_optimal_solutions": False,
        "error_message": result.get("error_message"),
    }
    return {
        "problem_type": result.get("problem_type", request.get("problem_type", "UNKNOWN")),
        "sub_type": _subtype(request, result),
        "status": result.get("status", "ERROR"),
        "objective": {"sense": objective_sense, "value": _rational(value)},
        "solution": {
            key: _rational(item) or item
            for key, item in (final.get("solution") or {}).items()
        },
        "iterations": iterations,
        "diagnostics": diagnostics,
        "final_result": rationalize(final),
        "sensitivity": rationalize(result.get("sensitivity")),
        "error_message": result.get("error_message"),
    }


def solve(request: dict[str, Any]) -> dict[str, Any]:
    started = perf_counter()
    result = Launcher().solve(request)
    return normalize_result(request, result, (perf_counter() - started) * 1000)


def examples() -> dict[str, dict[str, Any]]:
    return {name: rationalize(value) for name, value in EXAMPLES.items()}
