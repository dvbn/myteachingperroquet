# Phase 1 Decision Gates

Phase 1 is designed to stop before bad material propagates.

## Gate 0: Source Inventory Approval

Human checks:

- Are all expected raw files present?
- Are duplicates identified?
- Are known bad folders quarantined?
- Are source owners/instructors labeled correctly?

Required artifact: `SOURCE_INVENTORY.md`.

## Gate 1: Session Map Approval

Human checks:

- Are sessions/topics organized by pedagogical theme, not misleading file
  numbering?
- Are alternate instructor materials routed by content?
- Do approved overlapping sources have a clear unified topic corpus plan?
- Are prerequisites and forward-reference boundaries correct?

Required artifact: `SESSION_MAP.md`.

## Gate 2: Source Tier Approval

Human checks:

- Which sources are canonical?
- Which sources are authoring-only?
- Which sources are quarantined?
- Are lecture notes or transcripts admitted only as targeted excerpts?

Required artifacts:

- `LECTURE_SOURCE_TAGS.md`
- `ASSESSMENT_SOURCE_MANIFEST.md`
- `SUPPLEMENT_SOURCE_MANIFEST.md`
- `QUARANTINE_MANIFEST.md`

## Gate 3: Human-Verification Corpus Approval

Human checks:

- Are converted lectures readable?
- Are source slices assigned to the right session?
- Are approved raw lecture/source variants merged into a coherent unified
  topic corpus?
- Are exam examples representative?
- Are authoring-only and generated scaffolds clearly tagged?
- Are graphical-analysis guide/constraints suitable for the course?

Required artifact: `human-verification/README.md`.

## Gate 4: Downstream Preflight Approval

Automated checks:

- `moreexercices-input/course_config.json` loads.
- `example_files` resolve.
- TA preflight returns 0 failures.
- TA chunker produces non-empty lecture chunks.
- TA lecture files are unified topic corpus files and not raw source/instructor
  splits.
- Verified exercise JSON, if present, transforms cleanly.
- `DOWNSTREAM_CHANGE_REQUESTS.md` exists, even if empty.

TA preflight and chunking here are dry-runs over `ta-llm-input/`. They do not
modify the live TA index or deploy anything.

Required artifact: `PREFLIGHT_REPORT.md`.

## Gate 5: Workflow Alignment Checkpoint

This is the end of Phase 1.

Human checks:

- Is the corpus approved for downstream use?
- Are blocking downstream change requests identified?
- Should any `quiz-llm-bank` schema, type, validator, or prompt change be made
  before generation?
- Should any `ta-llm-system` schema, chunking, source-layout, or ingestion
  change be made before TA loading?
- Is the next step a sample generation, downstream patching, or a Phase 1 rerun?

Required artifacts:

- `APPROVAL.json` at `courses/<course_id>/phase1-output/APPROVAL.json`
- optional `human-verification/HUMAN_APPROVAL.md` review notes
- `DOWNSTREAM_CHANGE_REQUESTS.md`

## After Phase 1

These actions are deliberately outside this phase:

- run a small `moreexercices` sample generation;
- human-review generated sample exercises;
- implement approved downstream changes;
- run full `moreexercices` generation/validation/audit/fix;
- copy canonical lectures plus verified exercise bank into `ta-llm-system`;
- run TA `preflight`, `chunk`, `transform`, `rebuild`, and embeddings.
