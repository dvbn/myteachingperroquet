# Claude Prompt: Handoff Audit

You are Claude Opus 4.7 acting as an independent downstream handoff auditor.

Do not edit files.

Inspect the Phase 1 outputs for both consumers:

- `moreexercices-input`
- `ta-llm-input`
- `human-verification`
- `DOWNSTREAM_CHANGE_REQUESTS.md`

Verify:

- `moreexercices-input/course_config.json` contains required fields;
- `example_files` resolve;
- `inbox_files` resolve or default `Slides` fallback resolves;
- `Slides` and TA lecture files contain the unified topic corpus by default,
  not raw source/instructor splits;
- TA lectures contain only canonical or approved content;
- authoring-only materials are excluded from TA retrieval;
- manifests explain provenance and risks;
- human-verification files are readable and complete.
- downstream change requests are explicit and not hidden in prose.

Return:

- blocking issues;
- non-blocking risks;
- downstream changes that should be recorded before Phase 1 closes;
- required commands to run next;
- whether the user must manually review before proceeding.
