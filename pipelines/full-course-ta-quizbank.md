# Pipeline: Full Course TA + Quizbank

Use this when the instructor wants the complete workflow from raw teaching dump
to a TA assistant with optional quiz mode.

## Inputs

```text
courses/<course_id>/raw/
```

Optional:

- existing syllabus/session map;
- preferred branding;
- LLM provider choices;
- Netlify site or deployment target.

## Steps

1. Explore the raw dump.
2. Build the unified topic corpus plan when multiple source families cover the
   same course material. The default downstream corpus is one coherent course
   voice by session/topic, not raw streams split by instructor or source.
3. Audit assessment/practice style from actual content: exams, corrections,
   question pools, assignments, cases, figures, graphs, and representative
   lecture/slide material. Record this in `ASSESSMENT_STYLE_AUDIT.md`,
   including which question types are short enough for TA quiz mode.
4. Ask the compact upfront decision packet from
   `phase1-corpus-prep/STARTUP_QUESTION_BANK.md`, covering Phase 1 corpus,
   Phase 2 quizbank, Phase 3 TA behavior/runtime, and deployment defaults.
5. Write `workflow_config.json`.
6. Write a phase plan and wait for setup approval at
   `courses/<course_id>/APPROVAL.setup.json`.
7. Run Phase 1 corpus prep and stop for approval at
   `courses/<course_id>/phase1-output/APPROVAL.json`.
8. Run Phase 2 smoke quizbank and stop for approval at
   `courses/<course_id>/phase2-output/smoke/APPROVAL.json`.
9. Run Phase 2 full quizbank generation, validation, audit, fix, catalog, and
   stop for approval at `courses/<course_id>/phase2-output/full/APPROVAL.json`.
10. Run Phase 3 TA ingestion locally and stop for approval at
   `courses/<course_id>/phase3-output/ingestion/APPROVAL.json`.
11. Run deployment preview if requested and stop for approval at
   `courses/<course_id>/phase3-output/deployment-preview/APPROVAL.json`.
12. Deploy to production only after explicit approval at
    `courses/<course_id>/phase3-output/production/APPROVAL.json`.

## Mandatory Checkpoints

- Setup and phase plan.
- Source inventory, session map, and unified topic corpus plan.
- Assessment-style audit before quiz defaults.
- Explicit Phase 2 output shape: smoke/full counts, exercise types, per-type
  quotas, and quiz-visible types.
- Explicit Phase 3 setup: TA persona/source strictness, ingestion scope,
  quiz-mode UX, runtime provider, embeddings, auth, deployment target, secrets,
  allowed origin, and budget defaults.
- TA quiz mode suitability before exposing exercise types in the chatbot.
- Source tiering and quarantine.
- Human-verification corpus.
- Quizbank smoke sample.
- Full quizbank validation/audit/fix.
- TA ingestion build.
- Deployment preview.

## Review Checklists

Use:

- `pipelines/PIPELINE_CONTRACT.md`
- `checklists/source-safety.md`
- `checklists/phase1-corpus-review.md`
- `checklists/quizbank-validation.md`
- `checklists/ta-ingestion.md`
- `checklists/deployment.md`

## Success Criteria

- Approved Phase 1 handoff packages exist.
- Quizbank validators and audits have no unresolved blockers.
- TA preflight, chunk, transform, rebuild, and vectors pass.
- Student-facing TA excludes authoring-only and quarantined material.
- Instructor has approved deployment or local-only use.
