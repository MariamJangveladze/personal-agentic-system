"""Small command-line interface for local demos and smoke testing."""

import argparse
import json

from personal_agentic_system.memory import MemoryStore
from personal_agentic_system.workflow import ApprovalWorkflow


def main() -> None:
    parser = argparse.ArgumentParser(description="Personal Agentic System")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("index")
    search = subparsers.add_parser("search")
    search.add_argument("query")
    draft = subparsers.add_parser("draft")
    draft.add_argument("objective")
    approve = subparsers.add_parser("approve")
    approve.add_argument("run_id")
    approve.add_argument("--reviewer", required=True)
    approve.add_argument("--reason", default="")
    reject = subparsers.add_parser("reject")
    reject.add_argument("run_id")
    reject.add_argument("--reviewer", required=True)
    reject.add_argument("--reason", required=True)
    subparsers.add_parser("metrics")

    args = parser.parse_args()
    memory = MemoryStore()
    workflow = ApprovalWorkflow(memory=memory)

    if args.command == "index":
        result = memory.index_vault()
    elif args.command == "search":
        result = memory.search(args.query)
    elif args.command == "draft":
        result = workflow.create_draft(args.objective).model_dump(mode="json")
    elif args.command == "approve":
        result = workflow.approve(args.run_id, args.reviewer, args.reason).model_dump(mode="json")
    elif args.command == "reject":
        result = workflow.reject(args.run_id, args.reviewer, args.reason).model_dump(mode="json")
    else:
        result = workflow.metrics()

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

