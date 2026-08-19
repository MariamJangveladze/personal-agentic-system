# Reusable agent workflow specification

## 1. Outcome

Describe the business artifact the workflow produces and who uses it.

## 2. Trigger and inputs

- Triggering user or system
- Required inputs and validation rules
- Data classification and prohibited inputs

## 3. Agent permissions

List what each probabilistic component may retrieve, propose, classify, or draft.

## 4. Deterministic controls

Define the code-enforced state machine, authorization checks, idempotency rules,
timeouts, and permitted write targets.

## 5. Human approval

- Which decisions require approval
- What evidence the reviewer sees
- Reviewer identity requirements
- Rejection and revision behavior

## 6. Memory and retrieval

Document the source of truth, embedding model, index lifecycle, source citations,
and rules for preventing sensitive data from entering derived stores.

## 7. Observability and attribution

Capture run ID, model/provider, latency, token or local-compute attribution,
retrieved sources, state transitions, errors, reviewer, and outcome.

## 8. Evaluation

Define golden scenarios, factuality/source-grounding checks, unsafe-action tests,
approval bypass tests, latency target, and cost ceiling.

## 9. Release guardrails

- No secrets or real customer data in Git
- Tests prove that approval cannot be bypassed
- Generated indexes can be rebuilt from documented source data
- Rollback and operator instructions exist

