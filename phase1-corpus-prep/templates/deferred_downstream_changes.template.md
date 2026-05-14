# Deferred Downstream Change Requests

Phase 1 records these requests but does not implement them until the final
workflow-alignment checkpoint.

## Summary

| ID | Consumer | Blocking | Status | Title |
|---|---|---:|---|---|
| DCR-001 | `quiz-llm-bank` | yes/no | proposed | Short title |

## DCR-001: Short Title

Consumer:

- `quiz-llm-bank`
- `ta-llm-system`
- both

Blocking:

- `yes` if this must be fixed before running the next pipeline step;
- `no` if this is an improvement or later hardening task.

Evidence from Phase 1:

- source path or generated artifact path;
- exact failure, limitation, or mismatch;
- example session/topic affected.

Proposed downstream change:

- concise description of the required schema, validator, prompt, UI, chunking,
  or ingestion change.

Phase 1 workaround:

- what Phase 1 emitted for now;
- what was excluded or quarantined to avoid silent errors.

Owner/checkpoint:

- who should approve the change;
- when it should be implemented.

