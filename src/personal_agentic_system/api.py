"""FastAPI control surface for memory and approval-gated runs."""

import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from personal_agentic_system.config import settings
from personal_agentic_system.memory import MemoryStore
from personal_agentic_system.workflow import ApprovalWorkflow


class DraftRequest(BaseModel):
    objective: str = Field(min_length=5, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


class ReviewRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=200)
    reason: str = Field(default="", max_length=2000)


class RejectionRequest(ReviewRequest):
    reason: str = Field(min_length=3, max_length=2000)


def create_app(
    workflow: ApprovalWorkflow | None = None,
    memory: MemoryStore | None = None,
    control_token: str | None = None,
) -> FastAPI:
    memory_store = memory or MemoryStore()
    run_workflow = workflow or ApprovalWorkflow(memory=memory_store)
    app = FastAPI(
        title="Personal Agentic System",
        version="0.2.0",
        description="Local-first agent workflow with deterministic approval controls.",
    )
    expected_token = settings.api_control_token if control_token is None else control_token

    def require_control_token(
        authorization: Annotated[str | None, Header()] = None,
    ) -> None:
        if not expected_token:
            raise HTTPException(
                status_code=503,
                detail="Set API_CONTROL_TOKEN before using control endpoints",
            )
        scheme, _, supplied = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not secrets.compare_digest(
            supplied, expected_token
        ):
            raise HTTPException(status_code=401, detail="Invalid control token")

    @app.get("/health", tags=["operations"])
    def health() -> dict[str, str]:
        return {"status": "healthy", "service": "personal-agentic-system"}

    @app.post("/v1/memory/index", tags=["memory"], dependencies=[Depends(require_control_token)])
    def index_vault() -> dict[str, int]:
        return memory_store.index_vault()

    @app.get("/v1/memory/search", tags=["memory"], dependencies=[Depends(require_control_token)])
    def search_memory(
        query: Annotated[str, Query(min_length=2, max_length=2000)],
        top_k: Annotated[int, Query(ge=1, le=20)] = 5,
    ) -> list[dict[str, str | float]]:
        return memory_store.search(query, top_k)

    @app.post(
        "/v1/runs",
        status_code=status.HTTP_201_CREATED,
        tags=["workflow"],
        dependencies=[Depends(require_control_token)],
    )
    def create_draft(request: DraftRequest) -> dict:
        return run_workflow.create_draft(
            request.objective, top_k=request.top_k
        ).model_dump(mode="json")

    @app.get("/v1/runs/{run_id}", tags=["workflow"], dependencies=[Depends(require_control_token)])
    def get_run(run_id: str) -> dict:
        try:
            return run_workflow.load(run_id).model_dump(mode="json")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Run not found") from exc

    @app.post("/v1/runs/{run_id}/approve", tags=["workflow"], dependencies=[Depends(require_control_token)])
    def approve_run(run_id: str, request: ReviewRequest) -> dict:
        try:
            return run_workflow.approve(
                run_id, request.reviewer, request.reason
            ).model_dump(mode="json")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Run not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/v1/runs/{run_id}/reject", tags=["workflow"], dependencies=[Depends(require_control_token)])
    def reject_run(run_id: str, request: RejectionRequest) -> dict:
        try:
            return run_workflow.reject(
                run_id, request.reviewer, request.reason
            ).model_dump(mode="json")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Run not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/v1/metrics", tags=["operations"], dependencies=[Depends(require_control_token)])
    def metrics() -> dict[str, int | float]:
        return run_workflow.metrics()

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)


if __name__ == "__main__":
    main()
