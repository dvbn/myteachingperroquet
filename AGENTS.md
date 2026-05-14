# Agent Instructions

You are helping an instructor turn teaching material into a verified TA corpus
and quizbank. The user may not know the command line. Your job is to guide the
workflow, not to bypass the instructor.

## Required Reading

Before acting, read:

1. `README.md`
2. `pipelines/PIPELINE_CONTRACT.md` for the canonical checkpoint and approval-file scheme.
3. `phase1-corpus-prep/STARTUP_QUESTION_BANK.md`
4. The selected recipe under `pipelines/`
5. Relevant phase contracts:
   - `phase1-corpus-prep/HANDOFF_CONTRACTS.md`
   - `phase2-quizbank/quiz-llm-bank/README.md`
   - `phase3-ta-llm-system/README.md`

## Operating Loop

1. Explore the source dump first.
2. Report inferred facts and unresolved uncertainties.
3. Ask triggered questions from the startup question bank. For full-pipeline
   runs, ask one compact upfront decision packet covering Phase 1, Phase 2,
   Phase 3, and deployment; phase approvals still happen later at their gates.
4. Write a concrete phase-by-phase plan.
5. Wait for user approval before production work.
6. Run exactly one phase at a time.
7. Produce review artifacts and stop at each mandatory checkpoint.
8. Do not continue unless the relevant `APPROVAL.json` is approved.

## Guardrails

- Keep the human in the pilot seat. Surface uncertainty before acting.
- Never silently promote source material into student-facing TA retrieval.
- Never put exams, corrections, answer keys, rubrics, or authoring guides into
  TA lecture retrieval.
- Quarantine transcripts, AI summaries, noisy lecture notes, duplicates,
  spreadsheets, and personal/sensitive data by default. Admit a spreadsheet
  only if the user explicitly identifies it as a course dataset rather than a
  gradebook/export.
- Do not publish or commit private course materials, student data, secrets,
  deployment keys, or assessment keys.
- Do not silently substitute another model when the user selected a verifier or
  generator. Stop and explain the credential/model blocker.
- Do not propose or write quizbank type mix, math level, difficulty, or solution
  style until you have inspected actual assessment/practice content. Folder
  names and academic domain labels are not enough.
- Record all manual decisions in config, manifests, or approval artifacts; do
  not rely on chat history.
- When multiple approved course sources overlap, produce one unified
  topic-organized course corpus per session. Do not feed raw instructor/source
  splits to quiz generation or TA retrieval.

## Unified Corpus Default

The default Phase 1 output is a unified, source-grounded course corpus. It is
not one file per instructor, one stream per slide deck, or a bag of raw notes.
Merge approved source variants by normalized topic and write in one coherent
course voice. Preserve provenance and conflicts in manifests, not in
student-facing headings.

If sources disagree, record the conflict and ask about precedence. If one
source is outdated or unsafe, route it to authoring-only or quarantine. Do not
ask whether the default downstream corpus should be split by instructor; it
should not.

## Content Evidence Gate

Before `exercise_profile` is considered ready, produce or update
`ASSESSMENT_STYLE_AUDIT.md` with concrete sampled paths and observations from:

- canonical slides/lecture notes across the course;
- each approved source family when variants are merged;
- exams, corrections, question pools, assignments, rubrics, or exercise files;
- cases, readings, figures/graphs, games, datasets, or software material when
  present.

The audit controls Phase 2 defaults. If exams mostly contain open case or
graphical analysis questions, do not use math-heavy defaults. If the audit is
incomplete, keep `exercise_profile.basis` as
`pending_assessment_style_audit` and ask the user which material to inspect.

Before Phase 2 generation, explicitly confirm the output shape: smoke count
per session/language, full-run count per session/language, enabled exercise
types, per-type quotas, quiz-visible types, and any per-session overrides.

For full-pipeline setup, also confirm Phase 3 choices upfront when possible:
TA persona/source strictness, ingestion scope, quiz-mode UX, runtime provider,
embedding provider, auth, deployment target, required secrets, allowed origin,
and budget defaults. These are configuration decisions, not approval to ingest
or deploy.

## TA Runtime Shape

The deployed `course_ta` is not an exam grader. Its actual runtime prompt in
`phase3-ta-llm-system/netlify/functions/ta-chat.mjs` limits answers to about
200 words, 2-3 short prose paragraphs, no bullets/lists/headings/emojis, and
hints instead of homework solutions.

When building a quizbank that will feed TA quiz mode, distinguish:

- private assessment-style generation for calibration and verification;
- quiz-visible exercises that fit short chat turns;
- long essay, long passage-analysis, or rubric-heavy material that should be
  shortened into case/application prompts or hidden from quiz mode.

## Phase Boundaries

Setup / Phase 0 explores sources, resolves startup questions, writes
`workflow_config.json`, writes a phase plan, and stops at
`courses/<course_id>/APPROVAL.setup.json`.

Phase 1 emits verified handoffs. It does not generate the full quizbank or
ingest into TA.

Phase 2 generates and verifies exercises. It does not deploy.

Phase 3 copies approved lectures and verified exercises into `ta-llm-system`,
then runs local ingestion/build commands.

Deployment happens only after a successful local or preview build and explicit
production approval.

## Default Model Roles

- Orchestrator: the agent the user opened the repo with.
- Quiz generation: Claude Opus 4.7 by default in a generation agent/session.
- Quiz verification: Claude Opus 4.7 by default in a separate fresh-context
  verifier agent/session. Codex or another model may be added as a second
  verifier when available.
- TA runtime: provider-dependent; Mistral Medium on the default
  OpenAI-compatible Mistral path, switchable through TA env vars.
- Embeddings: OpenAI embeddings, required by the current TA pipeline.

If a sibling model is requested and fails, diagnose the failure. Do not replace
that model's perspective with your own.

For Phase 2, never let the same agent conversation both generate and verify
the same exercise batch. Same model is acceptable; same context is not.

## Output Bundle

For each course, maintain a local bundle under `courses/<course_id>/` using the
templates in `templates/`:

- `USER_GUIDE.md`
- `VERIFICATION.md`
- `SOURCE_NOTES.md`
- `ASSESSMENT_STYLE_AUDIT.md`
- `DEPLOYMENT.md`
- `PRIVACY.md`
- `COST_NOTES.md`
- `APPROVAL.json` per phase

Use the checklists in `checklists/` when writing verification notes.

## Canonical Approval Files

- Setup / plan: `courses/<course_id>/APPROVAL.setup.json`
- Phase 1 corpus: `courses/<course_id>/phase1-output/APPROVAL.json`
- Phase 2 smoke: `courses/<course_id>/phase2-output/smoke/APPROVAL.json`
- Phase 2 full: `courses/<course_id>/phase2-output/full/APPROVAL.json`
- Phase 3 ingestion: `courses/<course_id>/phase3-output/ingestion/APPROVAL.json`
- Preview deployment: `courses/<course_id>/phase3-output/deployment-preview/APPROVAL.json`
- Production deployment: `courses/<course_id>/phase3-output/production/APPROVAL.json`
