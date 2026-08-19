"""MCP surface for retrieval and approval-gated artifact creation."""

import json

from mcp.server.fastmcp import FastMCP

from personal_agentic_system.memory import MemoryStore
from personal_agentic_system.workflow import ApprovalWorkflow

mcp = FastMCP("personal-agentic-system")
memory = MemoryStore()
workflow = ApprovalWorkflow(memory=memory)


@mcp.tool()
def index_vault() -> str:
    """Index the configured safe Markdown vault using local Ollama embeddings."""
    return json.dumps(memory.index_vault(), indent=2)


@mcp.tool()
def memory_search(query: str, top_k: int = 5) -> str:
    """Search the local vault and return source-attributed context."""
    return json.dumps(memory.search(query, top_k), indent=2, ensure_ascii=False)


@mcp.tool()
def create_draft(objective: str) -> str:
    """Create a draft and pause it for explicit human approval."""
    return workflow.create_draft(objective).model_dump_json(indent=2)


@mcp.tool()
def approve_draft(run_id: str, reviewer: str, reason: str = "") -> str:
    """Approve one pending draft and deterministically write its artifact."""
    return workflow.approve(run_id, reviewer, reason).model_dump_json(indent=2)


@mcp.tool()
def reject_draft(run_id: str, reviewer: str, reason: str) -> str:
    """Reject one pending draft without writing an artifact."""
    return workflow.reject(run_id, reviewer, reason).model_dump_json(indent=2)


@mcp.tool()
def workflow_metrics() -> str:
    """Return run, approval, latency, and cost-attribution metrics."""
    return json.dumps(workflow.metrics(), indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

