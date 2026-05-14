---
description: Start the MyTeachingPerroquet workflow on a teaching-material dump
argument-hint: <path-to-dump>
---

# Start Dump Workflow

Use this command when the user wants to start from a raw teaching-material
dump. `$ARGUMENTS` should be the dump path. If `$ARGUMENTS` is empty, ask for
the path and do nothing else.

## Required Behavior

1. Read these files before making a plan:
   - `README.md`
   - `CLAUDE.md`
   - `pipelines/PIPELINE_CONTRACT.md`
   - `pipelines/full-course-ta-quizbank.md`
   - `phase1-corpus-prep/STARTUP_QUESTION_BANK.md`
   - `phase1-corpus-prep/PHASE1_SPEC.md`
   - `phase1-corpus-prep/HANDOFF_CONTRACTS.md`
   - `phase3-ta-llm-system/README.md`
   - `phase3-ta-llm-system/netlify/functions/ta-chat.mjs` (system-prompt
     defaults and runtime limits)
2. Inspect the dump contents directly. Do not rely on directory names alone.
3. Produce the pre-question exploration report required by
   `phase1-corpus-prep/STARTUP_QUESTION_BANK.md`.
4. When multiple course sources cover the same topic, propose a unified topic
   corpus map. The default is one source-grounded course voice by topic, not
   separate downstream corpora by instructor, deck, raw filename, or source
   family.
5. Before proposing exercise types, counts, or difficulty, produce an
   assessment-style audit from actual content:
   - inspect representative lecture/slide material from each candidate
     canonical source family;
   - inspect representative exams, corrections, question pools, assignments,
     cases, rubrics, and exercise files when present;
   - identify whether the course uses open questions, graphical analysis,
     case/source analysis, true/false, calculations, software output, or other
     formats;
   - distinguish private assessment style from TA quiz-visible style; long
     exam essays or passage analysis must be shortened or hidden for the
     short-form chatbot unless the user explicitly approves otherwise;
   - cite sampled paths and observed evidence.
6. If the user requested the full TA plus quizbank workflow, ask one compact
   upfront decision packet covering Phase 1 corpus, Phase 2 quizbank, Phase 3
   TA ingestion/runtime, and deployment defaults. Otherwise ask only the
   highest-impact unresolved question first.
7. Do not write generated corpus, quizbank, TA data, vectors, or deployment
   files during the first pass.

## Hard Blocks

- Do not infer the quizbank profile from the academic domain alone.
- Do not use the generic quantitative/qualitative defaults until the
  assessment-style audit exists.
- Do not ask whether approved overlapping sources should be split by
  instructor/source for downstream use. They should be merged into the unified
  topic corpus by default.
- Do not treat setup-time Phase 3 runtime/deployment preferences as approval
  to ingest, preview-deploy, or production-deploy. Those approvals stay gated.
- Do not promote transcripts, corrections, answer keys, or private assessment
  material into TA retrieval.
- Do not proceed past setup without `courses/<course_id>/APPROVAL.setup.json`
  explicitly approved.

## Expected First Output

Return:

```text
Exploration report:
- likely course:
- likely sessions:
- candidate canonical sources:
- candidate unified topic corpus map:
- candidate authoring-only sources:
- quarantine candidates:
- detected software/math/graphical/case components:
- assessment-style evidence sampled:
- unresolved decisions:
- upfront decision packet if full workflow requested:

Next question(s):
<full upfront decision packet for full workflow, otherwise one focused question>
```
