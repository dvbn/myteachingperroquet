# Pipeline Contract

Every public pipeline recipe in this repository follows this contract.

## Controlled Loop

1. Explore sources before asking questions.
2. Ask triggered questions from `phase1-corpus-prep/STARTUP_QUESTION_BANK.md`.
   For full-pipeline runs, ask the compact upfront decision packet covering
   Phase 1, Phase 2, Phase 3, and deployment configuration.
3. Plan the unified topic corpus when overlapping course sources exist.
4. Audit assessment/practice style from actual content before setting quizbank
   defaults.
5. Write a plan with assumptions, defaults, model choices, source policy,
   phase outputs, and checkpoints.
6. Wait for user approval.
7. Execute the approved phase only.
8. Write verification notes and update approval artifacts.
9. Stop before the next phase.

## Required Outputs

Each run should maintain these files under `courses/<course_id>/`:

```text
workflow_config.json
USER_GUIDE.md
VERIFICATION.md
SOURCE_NOTES.md
ASSESSMENT_STYLE_AUDIT.md
DEPLOYMENT.md
PRIVACY.md
COST_NOTES.md
```

Each phase emits or updates:

```text
APPROVAL.json
```

Automation may continue only when the relevant approval file has:

```json
{"status": "approved"}
```

## Canonical Checkpoints And Approval Files

Use these exact approval locations. Do not reuse one approval file for multiple
gates.

| Gate | `phase` value | Approval file | Allows |
|---|---|---|---|
| Setup / plan | `setup` | `courses/<course_id>/APPROVAL.setup.json` | Phase 1 corpus prep |
| Phase 1 corpus | `phase1` | `courses/<course_id>/phase1-output/APPROVAL.json` | Phase 2 smoke quizbank |
| Phase 2 smoke | `phase2-smoke` | `courses/<course_id>/phase2-output/smoke/APPROVAL.json` | Phase 2 full quizbank |
| Phase 2 full | `phase2-full` | `courses/<course_id>/phase2-output/full/APPROVAL.json` | Phase 3 TA ingestion |
| Phase 3 ingestion | `phase3-ingestion` | `courses/<course_id>/phase3-output/ingestion/APPROVAL.json` | Deployment preview |
| Preview deployment | `deployment-preview` | `courses/<course_id>/phase3-output/deployment-preview/APPROVAL.json` | Production deployment consideration |
| Production deployment | `production` | `courses/<course_id>/phase3-output/production/APPROVAL.json` | `netlify deploy --prod` |

Missing approval, invalid JSON, wrong phase, or any status other than
`approved` is blocking.

## Phase 0 Scope

Setup / Phase 0 is a real gate. It includes:

- raw-dump exploration report;
- triggered startup questions;
- `workflow_config.json`;
- source policy defaults and overrides;
- unified topic corpus plan when multiple source families cover the same
  course material;
- assessment-style audit based on sampled exams, cases, figures, assignments,
  and practice material;
- model/provider choices and credential blockers;
- branding defaults or user branding;
- Phase 3 TA behavior, ingestion scope, runtime provider, auth, deployment
  target, secret checklist, allowed origin, and budget defaults when the full
  TA workflow is requested;
- phase plan and first-run scope.

Phase 1 cannot start until setup approval is recorded.

Setup decisions do not replace phase approvals. Recording Phase 3 runtime or
deployment preferences during setup does not authorize TA ingestion, preview
deployment, or production deployment.

## Standard Source Policy

- `canonical`: approved course truth; eligible for TA retrieval and quiz content boundary.
- `supplement`: useful but secondary; authoring-only unless approved for TA.
- `assessment_style`: exams, corrections, rubrics; authoring-only.
- `case_source`: cases/readings/datasets; authoring-only unless assigned reading.
- `quarantine`: noisy, duplicate, generated, sensitive, uncertain; blocked.
- `generated_scaffold`: helper seeds/guides; authoring-only and never source truth.

Spreadsheets (`.xls`, `.xlsx`, `.xlsm`) are quarantine by default because they
often contain grades, rosters, exports, or private assessment data. Promote one
only if the user explicitly confirms it is a course dataset and approves the
downstream use. Raw dumps stay private and offline; only curated approved
corpus files and verified exercise/solution JSON are candidates for the
student-facing bot.

## Unified Corpus Policy

When multiple approved source families cover the same lecture or topic, Phase 1
must produce one unified, source-grounded course corpus by session/topic. Do
not emit separate downstream streams by instructor, deck, raw filename, term,
or source family.

The unified corpus is the default content boundary for both Phase 2 quiz
generation and Phase 3 TA retrieval. It should:

- merge by normalized pedagogical topic;
- use one coherent course voice suitable for students;
- deduplicate overlapping explanations, examples, figures, and cases;
- keep source precedence, conflicts, and provenance in manifests;
- surface real contradictions for user review rather than hiding them.

Ask the user about source precedence, unsafe material, outdated material, or
unresolved contradictions. Do not ask whether the default downstream corpus
should be split by instructor/source; it should not.

## Standard Bundle Files

- `USER_GUIDE.md`: how the instructor uses the outputs.
- `VERIFICATION.md`: what was checked, failures, residual risks, human tasks.
- `SOURCE_NOTES.md`: source boundaries and provenance without private excerpts.
- `ASSESSMENT_STYLE_AUDIT.md`: sampled evidence for exercise types, solution
  style, graph/case/open-question needs, TA quiz mode suitability, and Phase 2
  smoke defaults.
- `DEPLOYMENT.md`: local/deployment steps when relevant.
- `PRIVACY.md`: personal data, source rights, deployment exposure, LLM data flow.
- `COST_NOTES.md`: expected LLM/vector/deployment cost and budget toggles.

## Model Policy

Expose model choices in `workflow_config.json`. Do not silently substitute a
different model for a requested generator or verifier. If a selected model or
credential is unavailable, stop with a clear blocker.

Defaults:

- Quiz generation: Claude Opus 4.7.
- Quiz verification: Claude Opus 4.7 in a separate fresh-context verifier
  agent by default. Codex or another model may be added as a second verifier
  when available.
- TA chat/query runtime: provider-dependent; Mistral Medium for the default
  OpenAI-compatible Mistral path. Claude Haiku, OpenAI, Groq, or another
  compatible provider can be selected by environment variables.
- TA embeddings: OpenAI `text-embedding-3-small`, required by the current TA
  pipeline for vector builds and per-query retrieval embeddings.

These are separate systems. Phase 2 generation and verification may run inside
subscription-based agent tools such as Claude Desktop, Claude Code, Codex, or
another selected agent. The deployed TA uses API keys at runtime: one for
embeddings (`OPENAI_API_KEY`) and one for the chat/query model
(`MISTRAL_API_KEY` by default, or Anthropic/OpenAI/Groq settings if changed).

Phase 2 must separate roles:

- Generation agent: writes exercises and solutions.
- Verification agent: independently audits generated exercises and solutions
  after generation.
- The verifier may use the same model as the generator, but it must run in a
  separate agent/session without the generation conversation context.
- The orchestrator records which agent/model handled each role in the Phase 2
  verification notes.

## Exercise Profile Policy

Do not set `exercise_profile` from the course domain alone. The orchestrating
agent must inspect real assessment/practice evidence before proposing Phase 2
smoke defaults:

- current slides or lecture notes across the course;
- every approved source family when multiple variants are merged;
- exams, corrections, question pools, assignments, rubrics, and exercise files
  when present;
- cases, readings, figures, graphs, games, datasets, and software outputs when
  they appear pedagogically relevant.

The evidence is recorded in `ASSESSMENT_STYLE_AUDIT.md` and summarized in
`workflow_config.exercise_profile.assessment_style_evidence`. If the audit is
not done, keep `exercise_profile.basis` as
`pending_assessment_style_audit`, do not apply generic quantitative or
qualitative defaults, and ask the user which materials should drive the style.

Quiz-mode exercise types are inferred from the audit, not from the course
domain. If the sampled evidence contains yes/no or true/false questions,
multiple-choice questions, open short-answer questions, or case studies, the
proposed `exercise_types` should name those directly, for example `YES_NO`,
`MCQ`, `OPEN`, and `CASE`. Use `GRAPHICAL`, `CALCULATION`,
`SOURCE_ANALYSIS`, or course-specific types only when the evidence supports
them and they fit the short-form TA quiz-mode runtime.

Before Phase 2 generation starts, the user-facing plan must make the output
shape explicit:

- smoke exercises per session per language;
- full-run exercises per session per language;
- enabled exercise types;
- quiz-visible vs hidden/authoring-only types;
- per-session `type_distribution`, with totals matching `exercise_count`;
- any per-session count or type-mix overrides.

## Branding Policy

Default to deep navy, accent blue, teal, light blue, white, and neutral grays.
User-provided course or institution branding overrides these defaults.

## Private Material Policy

Keep private source dumps and generated course bundles in gitignored local
folders such as `courses/`, `work/`, `private_sources/`, or `local_sources/`.
Do not copy private source excerpts into public issues, examples, or docs.
