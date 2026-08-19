"""Tests prove that drafts cannot become artifacts without approval."""

from pathlib import Path

import pytest

from personal_agentic_system.config import Settings
from personal_agentic_system.models import RunStatus
from personal_agentic_system.workflow import ApprovalWorkflow


class FakeMemory:
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        return [{"source": "controls.md", "text": "Require human approval."}]


def build_workflow(tmp_path: Path) -> ApprovalWorkflow:
    config = Settings(
        chroma_path=tmp_path / "chroma",
        vault_path=tmp_path / "vault",
        runs_path=tmp_path / "runs",
    )
    return ApprovalWorkflow(
        config=config,
        memory=FakeMemory(),
        draft_fn=lambda objective, context: f"Draft for: {objective}",
    )


def test_draft_waits_for_approval_and_writes_no_artifact(tmp_path: Path) -> None:
    workflow = build_workflow(tmp_path)
    record = workflow.create_draft("Prepare a checklist")

    assert record.status == RunStatus.DRAFTED
    assert record.artifact_path is None
    assert not (tmp_path / "runs" / "artifacts").exists()


def test_named_reviewer_can_approve_once(tmp_path: Path) -> None:
    workflow = build_workflow(tmp_path)
    drafted = workflow.create_draft("Prepare a checklist")
    approved = workflow.approve(drafted.run_id, "Mariam", "Reviewed for demo")

    assert approved.status == RunStatus.APPROVED
    assert approved.reviewer == "Mariam"
    assert Path(approved.artifact_path).read_text() == "Draft for: Prepare a checklist\n"

    with pytest.raises(ValueError, match="already approved"):
        workflow.approve(drafted.run_id, "Another reviewer")


def test_rejection_requires_a_reason_and_writes_no_artifact(tmp_path: Path) -> None:
    workflow = build_workflow(tmp_path)
    drafted = workflow.create_draft("Prepare a checklist")

    with pytest.raises(ValueError, match="reason"):
        workflow.reject(drafted.run_id, "Mariam", "")

    rejected = workflow.reject(drafted.run_id, "Mariam", "Needs stronger evidence")
    assert rejected.status == RunStatus.REJECTED
    assert rejected.artifact_path is None

