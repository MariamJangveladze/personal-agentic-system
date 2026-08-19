# Architecture and boundaries

## Design intent

This repository turns selected MJ-OS patterns into a small system that an
interviewer can understand and run. It keeps the meaningful technical choices:
Ollama, Chroma, an Obsidian-compatible vault, MCP tools, traces, and approval gates.

## Trust boundaries

| Component | May do | Must not do |
|---|---|---|
| Retrieval | Select source passages | Change source notes |
| LLM drafting | Propose an artifact and assumptions | Approve or persist it |
| Reviewer | Approve or reject a pending run | Rewrite prior audit records |
| Deterministic workflow | Validate transitions and write approved output | Invent reviewer identity |
| Chroma | Store derived vectors and metadata | Become the canonical knowledge source |
| Telegram adapter | Submit objectives and approval decisions | Accept unknown chat IDs |

## Data classification

Only synthetic example notes belong in Git. A real vault, vector database, run
records, logs, Telegram tokens, and chat IDs remain local and are ignored.

## Hermes relationship

Hermes remains the operational agent interface in MJ-OS. This repository focuses
on the portable enterprise-control pattern: retrieval, proposal, approval,
deterministic commit, and traceability. A later adapter can surface these runs in
the Hermes dashboard rather than creating a competing general-purpose dashboard.

## Cost attribution

Each run stores its model, latency, and estimated API cost. The Ollama default is
recorded as `$0.00` API cost; that does not imply compute is free. Cloud adapters
should attribute input/output tokens, provider, model, request ID, and errors to
the same run record.

