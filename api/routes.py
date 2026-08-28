from __future__ import annotations

from fastapi import APIRouter

from schemas import SolverRequest, SolverResponse
from services import examples, solve

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "or-engine"}


@router.get("/examples")
def get_examples() -> dict[str, dict]:
    return examples()


@router.post("/solve", response_model=SolverResponse)
def post_solve(request: SolverRequest) -> dict:
    return solve(request.model_dump())
