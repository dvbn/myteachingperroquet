# Claude Prompt: Workflow Alignment Checkpoint Audit

You are Claude Opus 4.7 acting as an independent Phase 1 closure auditor.

Do not edit files.

Inspect:

- `APPROVAL.json`
- optional `human-verification/HUMAN_APPROVAL.md`
- `PREFLIGHT_REPORT.md`
- `DOWNSTREAM_CHANGE_REQUESTS.md`
- `moreexercices-input/course_config.json`
- `ta-llm-input/data/course_config.json`
- representative human-verification session files

Verify specifically that downstream lecture files are clean unified topic
corpus files and not raw source/instructor splits. Provenance may appear in
manifests, but should not create parallel student-facing lecture streams.

Decide whether Phase 1 is ready to close.

Return concise Markdown with:

- blocking issues before Phase 1 closure;
- downstream changes required before sample `moreexercices` generation;
- downstream changes required before TA ingestion;
- items the human reviewer must verify manually;
- the recommended next pipeline step.

Do not recommend running full generation until a small sample has been reviewed.
