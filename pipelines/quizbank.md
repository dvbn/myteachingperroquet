# Pipeline: Quizbank Generation

Use this when Phase 1 already produced an approved
`moreexercices-input/` package, or when the instructor has a prepared
`quiz-llm-bank` inbox and config.

## Inputs

```text
courses/<course_id>/phase1-output/moreexercices-input/
```

## Steps

1. Confirm Phase 1 approval at
   `courses/<course_id>/phase1-output/APPROVAL.json`.
2. Copy `moreexercices-input/course_config.json` and `inbox/` into
   `phase2-quizbank/quiz-llm-bank/`.
3. Confirm `assessment_style_basis` is resolved and, if the bank will feed TA
   quiz mode, confirm `quiz_mode_constraints` or equivalent course-bundle
   notes are present.
4. Generate schema.
5. Run prompt dry-run for selected smoke sessions.
6. Generate smoke exercises with the configured generation agent/session.
7. Validate, then audit smoke output with a separate fresh-context verifier
   agent/session. The verifier may use the same model, but not the same chat
   context as generation.
8. Stop for smoke approval at
   `courses/<course_id>/phase2-output/smoke/APPROVAL.json`.
9. Generate full bank with the configured generation agent/session.
10. Run all validators.
11. Run configured audits in independent verifier agent/session(s).
12. Rewrite, reclassify, or explicitly accept findings.
13. Generate catalog and review queue.
14. Stop for full-bank approval at
    `courses/<course_id>/phase2-output/full/APPROVAL.json` before TA ingestion.

## Commands

Run Phase 2 commands from:

```bash
cd phase2-quizbank/quiz-llm-bank
```

Examples:

```bash
python3 pipeline/schema_builder.py course_config.json
python3 pipeline/run.py --config course_config.json --dry-run --sessions S1
PYTHONPATH=pipeline python3 pipeline/validators/validate_schema.py course_config.json
PYTHONPATH=pipeline python3 pipeline/validators/validate_structure.py course_config.json
PYTHONPATH=pipeline python3 pipeline/validators/validate_coverage.py course_config.json
PYTHONPATH=pipeline python3 pipeline/validators/validate_bilingual.py course_config.json
PYTHONPATH=pipeline python3 pipeline/validators/validate_math.py course_config.json
PYTHONPATH=pipeline python3 pipeline/validators/validate_rag.py course_config.json
PYTHONPATH=pipeline python3 pipeline/validators/validate_content_boundary.py course_config.json
python3 pipeline/catalog_generator.py
```

## Stop Condition

Do not copy exercise JSON into `ta-llm-system` until the full bank has approved
validation, audit, fix, review artifacts, and quiz-visible type decisions.
