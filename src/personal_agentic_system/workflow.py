"""Approval-gated workflow: models draft; deterministic code authorizes writes."""

import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from personal_agentic_system.config import Settings, settings
from personal_agentic_system.gateway import GenerationResult, OllamaGateway
from personal_agentic_system.memory import MemoryStore
from personal_agentic_system.models import RunRecord, RunStatus


class ApprovalWorkflow:
    def __init__(
        self,
        config: Settings = settings,
        memory: MemoryStore | None = None,
        draft_fn: Callable[[str, list[dict]], str | GenerationResult] | None = None,
        gateway: OllamaGateway | None = None,
    ) -> None:
        self.config = config
        self.memory = memory or MemoryStore(config)
        self.draft_fn = draft_fn or self._draft_with_ollama
        self.gateway = gateway or OllamaGateway(config)

    def _run_path(self, run_id: str) -> Path:
        return self.config.runs_path / f"{run_id}.json"

    def _save(self, record: RunRecord) -> None:
        self.config.runs_path.mkdir(parents=True, exist_ok=True)
        self._run_path(record.run_id).write_text(
            record.model_dump_json(indent=2), encoding="utf-8"
        )

    def load(self, run_id: str) -> RunRecord:
        return RunRecord.model_validate_json(
            self._run_path(run_id).read_text(encoding="utf-8")
        )

    def _draft_with_ollama(
        self, objective: str, context: list[dict]
    ) -> GenerationResult:
        source_text = "\n\n".join(
            f"SOURCE: {item['source']}\n{item['text']}" for item in context
        )
        prompt = (
            "You are a careful enterprise AI assistant. Draft an actionable artifact "
            "for the objective using only relevant supplied context. Clearly mark any "
            f"assumptions.\n\nOBJECTIVE:\n{objective}\n\nCONTEXT:\n{source_text}"
        )
        return self.gateway.generate(prompt)

    def create_draft(self, objective: str, top_k: int = 5) -> RunRecord:
        started = time.perf_counter()
        context = self.memory.search(objective, top_k=top_k)
        draft_result = self.draft_fn(objective, context)
        generation = (
            draft_result if isinstance(draft_result, GenerationResult) else None
        )
        draft = generation.text if generation else draft_result
        record = RunRecord(
            objective=objective,
            model=generation.model if generation else self.config.chat_model,
            sources=sorted({str(item["source"]) for item in context}),
            draft=draft,
            latency_ms=round((time.perf_counter() - started) * 1000),
            # Ollama is local, so API cost is recorded as zero; hardware cost is out of scope.
            estimated_cost_usd=generation.estimated_cost_usd if generation else 0.0,
            metadata={
                "provider": generation.provider if generation else "test-or-custom",
                "input_tokens": generation.input_tokens if generation else None,
                "output_tokens": generation.output_tokens if generation else None,
                "model_latency_ms": generation.latency_ms if generation else None,
                "finish_reason": generation.finish_reason if generation else None,
            },
        )
        self._save(record)
        return record

    def approve(self, run_id: str, reviewer: str, reason: str = "") -> RunRecord:
        record = self.load(run_id)
        if record.status != RunStatus.DRAFTED:
            raise ValueError(f"Run {run_id} is already {record.status}")
        if not reviewer.strip():
            raise ValueError("A named reviewer is required")

        artifacts_path = self.config.runs_path / "artifacts"
        artifacts_path.mkdir(parents=True, exist_ok=True)
        artifact_path = artifacts_path / f"{record.run_id}.md"
        artifact_path.write_text(record.draft + "\n", encoding="utf-8")

        record.status = RunStatus.APPROVED
        record.reviewer = reviewer.strip()
        record.review_reason = reason.strip() or None
        record.artifact_path = str(artifact_path)
        record.updated_at = datetime.now(UTC)
        self._save(record)
        return record

    def reject(self, run_id: str, reviewer: str, reason: str) -> RunRecord:
        record = self.load(run_id)
        if record.status != RunStatus.DRAFTED:
            raise ValueError(f"Run {run_id} is already {record.status}")
        if not reviewer.strip() or not reason.strip():
            raise ValueError("Reviewer and rejection reason are required")

        record.status = RunStatus.REJECTED
        record.reviewer = reviewer.strip()
        record.review_reason = reason.strip()
        record.updated_at = datetime.now(UTC)
        self._save(record)
        return record

    def metrics(self) -> dict[str, int | float]:
        records = [
            RunRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self.config.runs_path.glob("*.json")
        ] if self.config.runs_path.exists() else []
        approved = sum(record.status == RunStatus.APPROVED for record in records)
        rejected = sum(record.status == RunStatus.REJECTED for record in records)
        return {
            "runs": len(records),
            "approved": approved,
            "rejected": rejected,
            "awaiting_approval": len(records) - approved - rejected,
            "average_latency_ms": (
                round(sum(record.latency_ms for record in records) / len(records), 2)
                if records else 0.0
            ),
            "estimated_cost_usd": round(
                sum(record.estimated_cost_usd for record in records), 6
            ),
        }
