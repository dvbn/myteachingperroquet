# Quizbank Validation Checklist

Use this for Phase 2 smoke and full quizbank approval.

## Smoke Review

- Smoke profile is justified by `ASSESSMENT_STYLE_AUDIT.md`.
- Exercise style matches course expectations.
- Exercise type codes come from observed assessment/practice evidence rather
  than generic course-domain assumptions.
- Yes/no, multiple-choice, open-ended, and case-study formats are represented
  explicitly as `YES_NO`, `MCQ`, `OPEN`, and `CASE` when the evidence supports
  them.
- Smoke and full-run counts per session per language are explicitly approved
  before generation.
- Each session's `type_distribution` sums to its `exercise_count`.
- Quiz-visible exercise types fit the TA runtime: short chat turns, hints
  before solutions, no long passage-analysis unless explicitly approved.
- Long essay/rubric-heavy/question-pool material is hidden from quiz mode or
  converted into short case/application prompts.
- Difficulty is appropriate for the audience.
- Hints are useful and do not reveal solutions too early.
- Solutions are concise and correct.
- Exercises stay within the session's content boundary.
- Bilingual twins, if enabled, are equivalent rather than loosely translated.
- The question-type mix is useful.
- Graphical, case/source-analysis, open written, math, true/false, and
  interpretation questions appear only in proportions justified by the audit.

## Automated Validators

All configured validators should pass or have approved non-blocking exceptions:

- schema;
- structure;
- coverage;
- bilingual;
- math;
- RAG readiness;
- content boundary.

## Audit Review

- Generation and verification were separate steps.
- The verifier ran in a fresh independent agent/session and did not reuse the
  generator's conversation context.
- The verifier model/agent identity is recorded, even when it is the same model
  family as the generator.
- CRITICAL findings are fixed, reclassified, or explicitly accepted.
- MAJOR findings are fixed, reclassified, or explicitly accepted.
- Deletions are user-approved.
- Reclassifications keep twin IDs and references consistent.
- Full run has a catalog and review sample.

## Output Evidence

- `output/<course_id>/schema.json`
- `output/<course_id>/<session_dir>/exercises_<LANG>.json`
- `output/<course_id>/validation/`
- `EXERCISE_BANK_CATALOG.md`
- review queue/log if used
- smoke gate: `courses/<course_id>/phase2-output/smoke/APPROVAL.json`
- full-bank gate: `courses/<course_id>/phase2-output/full/APPROVAL.json`
