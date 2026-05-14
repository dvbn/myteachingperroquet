# Workflow Tools

This directory contains lightweight helpers for the agent-guided workflow.
They do not replace the Phase 1, Phase 2, or Phase 3 systems. They provide the
glue needed for a controlled multi-phase run.

## Scaffold A Course Bundle

```bash
python3 tools/workflow/scaffold_course.py --course-id my_course_2026
```

This creates:

```text
courses/my_course_2026/
  raw/
  workflow_config.json
  APPROVAL.setup.json
  phase1-output/APPROVAL.json
  phase2-output/smoke/APPROVAL.json
  phase2-output/full/APPROVAL.json
  phase3-output/ingestion/APPROVAL.json
  phase3-output/deployment-preview/APPROVAL.json
  phase3-output/production/APPROVAL.json
  USER_GUIDE.md
  VERIFICATION.md
  SOURCE_NOTES.md
  ASSESSMENT_STYLE_AUDIT.md
  DEPLOYMENT.md
  PRIVACY.md
  COST_NOTES.md
```

Private source material belongs under `courses/<course_id>/raw/` or another
gitignored path.

## Check Approval Gates

```bash
python3 tools/workflow/check_approval.py \
  --approval courses/my_course_2026/phase1-output/APPROVAL.json \
  --phase phase1
```

Exit code is `0` only when the approval file exists at a canonical gate path,
its `phase` matches that path and the optional `--phase` argument, and
`status` is `approved`.

Canonical phase values are: `setup`, `phase1`, `phase2-smoke`, `phase2-full`,
`phase3-ingestion`, `deployment-preview`, and `production`.

## Future Drivers

These planned drivers are not shipped yet:

- `run_quizbank.py`
- `ingest_ta.py`
- `setup_course.py`

Those should wrap existing phase systems rather than reimplementing them.
