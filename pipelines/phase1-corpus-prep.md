# Pipeline: Phase 1 Corpus Prep Only

Use this when the instructor wants a clean, verified corpus and handoff package
before deciding whether to generate exercises or deploy a TA.

## Inputs

```text
courses/<course_id>/raw/
courses/<course_id>/workflow_config.json
```

## Steps

1. Explore all raw sources.
2. Inventory files, duplicates, owners, language, source type, and risks.
3. Inspect assessment/practice content before quiz defaults: exams,
   corrections, question pools, assignments, cases, figures, graphs, and
   representative lecture/slide material.
4. Write `ASSESSMENT_STYLE_AUDIT.md` with sampled paths and implications for
   Phase 2 smoke, including which exercise styles are suitable for the
   short-form TA quiz mode runtime.
5. Ask triggered source/session questions.
6. Normalize the session and topic map.
7. Convert approved sources to Markdown with provenance.
8. Route slices by topic.
9. Merge canonical lecture slices into one unified topic corpus per session.
10. Extract authoring-only examples into the `moreexercices` lane.
11. Emit `moreexercices-input/`.
12. Emit `ta-llm-input/`.
13. Emit manifests, verification corpus, preflight report, downstream change requests.
14. Stop for user approval at
    `courses/<course_id>/phase1-output/APPROVAL.json`.

## Outputs

```text
courses/<course_id>/phase1-output/
  human-verification/
  moreexercices-input/
  ta-llm-input/
  ASSESSMENT_STYLE_AUDIT.md
  PREFLIGHT_REPORT.md
  DOWNSTREAM_CHANGE_REQUESTS.md
  APPROVAL.json
```

## Required Contracts

Read:

- `phase1-corpus-prep/PHASE1_SPEC.md`
- `phase1-corpus-prep/HANDOFF_CONTRACTS.md`
- `phase1-corpus-prep/DECISION_GATES.md`

## Stop Condition

Do not run quiz generation or TA ingestion. Phase 1 approval only authorizes the
next phase; it is not implicit approval to deploy or publish.
