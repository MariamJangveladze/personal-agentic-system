"""API contract tests for health, retrieval of runs, and review transitions."""

from pathlib import Path

from fastapi.testclient import TestClient

from personal_agentic_system.api import create_app
from personal_agentic_system.config import Settings
from personal_agentic_system.workflow import ApprovalWorkflow


class FakeMemory:
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        return [{"source": "controls.md", "text": "Require approval."}]

    def index_vault(self) -> dict[str, int]:
        return {"notes": 1, "chunks": 1}


def build_client(tmp_path: Path) -> TestClient:
    config = Settings(runs_path=tmp_path / "runs")
    memory = FakeMemory()
    workflow = ApprovalWorkflow(
        config=config,
        memory=memory,
        draft_fn=lambda objective, context: f"Controlled draft: {objective}",
    )
    return TestClient(create_app(workflow=workflow, memory=memory, control_token="test-token"))


def auth() -> dict[str, str]:
    return {"Authorization": "Bearer test-token"}


def test_health_contract(tmp_path: Path) -> None:
    response = build_client(tmp_path).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_run_requires_review_before_artifact(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    created = client.post(
        "/v1/runs", json={"objective": "Prepare an exception checklist"}, headers=auth()
    )
    assert created.status_code == 201
    run = created.json()
    assert run["status"] == "drafted"
    assert run["artifact_path"] is None

    approved = client.post(
        f"/v1/runs/{run['run_id']}/approve",
        json={"reviewer": "portfolio-reviewer", "reason": "Evidence checked"},
        headers=auth(),
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert Path(approved.json()["artifact_path"]).exists()


def test_api_prevents_second_decision(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    run = client.post(
        "/v1/runs", json={"objective": "Prepare an exception checklist"}, headers=auth()
    ).json()
    client.post(
        f"/v1/runs/{run['run_id']}/reject",
        json={"reviewer": "portfolio-reviewer", "reason": "Insufficient evidence"},
        headers=auth(),
    )

    response = client.post(
        f"/v1/runs/{run['run_id']}/approve",
        json={"reviewer": "second-reviewer"},
        headers=auth(),
    )
    assert response.status_code == 409


def test_control_endpoints_require_token(tmp_path: Path) -> None:
    response = build_client(tmp_path).post(
        "/v1/runs", json={"objective": "Prepare an exception checklist"}
    )
    assert response.status_code == 401
