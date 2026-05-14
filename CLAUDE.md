# Claude Workflow Instructions

You are likely being used by an instructor through Claude Desktop cowork mode
or Claude Code. The instructor expects the repository to guide you. Do not make
them discover scripts or edit JSON by hand.

## First Response For A New Course

If the user says they dumped course material and wants the workflow:

1. Read `README.md`, `pipelines/PIPELINE_CONTRACT.md`,
   `phase1-corpus-prep/STARTUP_QUESTION_BANK.md`, the selected recipe under
   `pipelines/`, and the relevant phase contract README/spec files.
2. Inspect the dump path the user provided.
3. Summarize what you found: likely course, sessions, languages, canonical
   sources, authoring-only sources, quarantine candidates, software/math/data,
   assessment-style evidence sampled, and unresolved decisions.
4. If the user requested the full workflow, ask one compact upfront decision
   packet covering Phase 1, Phase 2, Phase 3, and deployment. Otherwise ask
   the highest-impact unresolved question first.
5. Build `courses/<course_id>/workflow_config.json` only after enough
   questions are resolved.
6. Write a phase plan and wait for setup approval at
   `courses/<course_id>/APPROVAL.setup.json`.

Do not start generation, TA ingestion, vector building, or deployment in the
first pass.

## Content-First Exercise Profile

Do not infer quizbank types, counts, difficulty, or solution style from the
course domain, folder names, or generic quantitative/qualitative defaults.
Before proposing an exercise profile, inspect actual content:

- representative slides or lecture notes from each approved source family;
- exams, corrections, question pools, assignments, rubrics, or exercise files
  when present;
- cases, readings, figures, graphs, datasets, games, or other practice
  material when present.

Write the evidence into `ASSESSMENT_STYLE_AUDIT.md` or the setup notes before
setting `exercise_profile`. If the evidence shows open questions, graphical
analysis, case studies, or little/no math, mirror that. If the evidence is
insufficient, mark `exercise_profile.basis` as `pending_assessment_style_audit`
and ask for the missing sources instead of applying defaults.

Before Phase 2 generation, explicitly confirm the output shape: smoke count
per session/language, full-run count per session/language, enabled exercise
types, per-type quotas, quiz-visible types, and any per-session overrides.

For full-pipeline setup, also confirm Phase 3 choices upfront when possible:
TA persona/source strictness, ingestion scope, quiz-mode UX, runtime provider,
embedding provider, auth, deployment target, required secrets, allowed origin,
and budget defaults. These are configuration decisions, not approval to ingest
or deploy.

## Question Discipline

Use `phase1-corpus-prep/STARTUP_QUESTION_BANK.md`. Ask one focused question at
a time for narrow tasks. For the full TA plus quizbank pipeline, ask the
upfront decision packet and let the user answer "keep defaults except ...".
Confirm inferred facts instead of asking from scratch.

## Unified Corpus Default

When multiple approved source families cover the same course material, Phase 1
must create one unified topic corpus per session before Phase 2 or Phase 3. Do
not pass separate instructor/deck/note streams into quiz generation or TA
retrieval. Merge by topic, deduplicate overlaps, keep one course voice, and put
source provenance/conflicts in manifests.

Ask the user about source precedence or contradictions only when the inspected
content conflicts. Do not ask whether raw source splits should be the default;
they should not.

## Mandatory Stops

Stop for user verification after:

- setup and phase plan;
- source inventory and session map;
- Phase 1 human-verification corpus and handoff packages;
- Phase 2 smoke quizbank;
- Phase 2 full validation/audit/fix;
- Phase 3 TA ingestion build;
- deployment preview.

Each stop should produce or update the gate-specific approval file defined in
`pipelines/PIPELINE_CONTRACT.md`. Treat missing approval as a blocker. Do not
reuse one approval file for multiple gates.

## Safety Defaults

- Student-facing TA retrieval gets canonical, approved lectures only.
- Exams/corrections/answer keys are authoring-only.
- Noisy notes, transcripts, generated summaries, duplicates, spreadsheets, and
  personal data are quarantined by default unless the user explicitly approves
  a specific spreadsheet as a course dataset.
- Bilingual generation is optional, not automatic unless clearly required.
- Production deployment requires explicit approval.

## TA Runtime Shape

Before deciding what belongs in the deployed TA or quiz mode, read
`phase3-ta-llm-system/netlify/functions/ta-chat.mjs` and
`phase3-ta-llm-system/README.md`. The default `course_ta` runtime is a short
conversational assistant: about 200 words, 2-3 prose paragraphs, no bullets,
no numbered lists, no headings, no emojis, and hints rather than homework
solutions.

Do not confuse exam style with chatbot style. Long passage-based text analysis,
full essay answers, and grading-rubric solutions may be useful for private
quizbank authoring or verification, but they should be adapted into short
case/application quiz questions or hidden from quiz mode unless the user
explicitly wants a long-form assessment bank outside the chatbot.

## Model And Credential Defaults

- Quiz generation: Claude Opus 4.7 in a generation agent/session.
- Quiz verification: Claude Opus 4.7 in a separate fresh-context verifier
  agent/session. Codex or another model may be added as a second verifier when
  available.
- TA runtime: provider-dependent; Mistral Medium on the default
  OpenAI-compatible Mistral path, switchable to Anthropic, OpenAI, or Groq.
- Embeddings: OpenAI embeddings are required by the current TA pipeline.

If a selected generator, verifier, or provider credential is unavailable, stop
and explain the blocker. Do not silently replace the selected model.

For Phase 2, do not verify exercises in the same conversation that generated
them. Start a fresh verifier context even when using Claude for both roles.

## Visual Defaults

When generating student-facing HTML or deployment materials, default to the
academic palette: deep navy, accent blue, teal, light blue, white, and neutral
grays. Use instructor-provided branding when available. Do not invent logos.
