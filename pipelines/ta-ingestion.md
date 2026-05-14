# Pipeline: TA Ingestion

Use this when Phase 1 lectures and, optionally, verified Phase 2 exercises are
ready to load into `ta-llm-system`.

## Inputs

```text
courses/<course_id>/phase1-output/ta-llm-input/
phase2-quizbank/quiz-llm-bank/output/<course_id>/
```

## Steps

1. Confirm Phase 1 approval at
   `courses/<course_id>/phase1-output/APPROVAL.json`.
2. Confirm Phase 2 full approval at
   `courses/<course_id>/phase2-output/full/APPROVAL.json` if quiz mode is
   enabled.
3. Copy approved lectures to `phase3-ta-llm-system/sources/lectures/`.
4. Copy approved `SOURCES.md`.
5. Copy TA course config to `phase3-ta-llm-system/data/course_config.json`.
6. Copy verified exercise JSON to `phase3-ta-llm-system/sources/exercises/`.
7. Run TA preflight and corpus build.
8. Review generated data files and stop for approval at
   `courses/<course_id>/phase3-output/ingestion/APPROVAL.json`.

## Commands

Run from:

```bash
cd phase3-ta-llm-system
```

Then:

```bash
npm run preflight
npm run chunk
npm run transform
npm run rebuild
npm run vectors
```

`npm run vectors` requires `OPENAI_API_KEY`.

## Safety Rules

- Do not copy exams, corrections, answer keys, authoring guides, or quarantined
  sources into `sources/lectures/`.
- Do not copy raw dumps or spreadsheets into the TA system. Only Phase 1
  approved lecture/corpus files and Phase 2 verified exercise JSON belong in
  the deployable tree.
- If `SOFTWARE` exercise JSON uses `software_code`, mirror it into
  `stata_code` until the TA transformer supports a generic software field.
- Quiz mode is enabled only when `data/exercise_index.json` is non-empty and
  based on approved exercises.

## Stop Condition

Do not deploy. TA ingestion approval authorizes deployment planning only.
