from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ProblemType = Literal["LP", "IP", "TP", "AP", "GT"]
SolverStatus = Literal[
    "OPTIMAL",
    "INFEASIBLE",
    "UNBOUNDED",
    "MAX_ITER_REACHED",
    "ERROR",
]


class RationalNumberDTO(BaseModel):
    display: str
    numerator: int
    denominator: int = Field(gt=0)
    decimal: float


class SolverRequest(BaseModel):
    problem_type: ProblemType
    payload: dict[str, Any]
    sub_type: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class ObjectiveDTO(BaseModel):
    sense: Literal["max", "min"] | None = None
    value: RationalNumberDTO | None = None


class DiagnosticsDTO(BaseModel):
    elapsed_ms: float = 0
    total_steps: int = 0
    degeneracy_detected: bool = False
    multiple_optimal_solutions: bool = False
    error_message: str | None = None


class SolverResponse(BaseModel):
    problem_type: str
    sub_type: str | None = None
    status: SolverStatus | str
    objective: ObjectiveDTO | None = None
    solution: dict[str, Any] = Field(default_factory=dict)
    iterations: list[dict[str, Any]] = Field(default_factory=list)
    diagnostics: DiagnosticsDTO = Field(default_factory=DiagnosticsDTO)
    final_result: dict[str, Any] = Field(default_factory=dict)
    sensitivity: dict[str, Any] | None = None
    error_message: str | None = None
