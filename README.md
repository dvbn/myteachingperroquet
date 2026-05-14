# MyTeachingPerroquet

MyTeachingPerroquet helps turn course material, documentation, or any bounded
knowledge collection into a student-facing teaching assistant and optional
quiz mode without requiring the user to understand chatbot internals,
embeddings, Netlify, or web deployment.

It is an interactive workflow for educators, teaching teams, instructional
designers, departments, researchers, documentation maintainers, and anyone who
has source material and wants a careful way to build a grounded AI companion
from it. You put the material in a folder, open the repository with a coding
agent such as Claude Code, Codex, or another capable assistant, and answer
plain-language questions. The agent explores the files, proposes a plan, builds
the corpus, generates and verifies exercises if needed, prepares the TA system,
and stops at approval gates.

The important idea is simple: the AI does the technical work, but the educator
stays in control. The workflow is designed so source choices, pedagogy,
privacy, quiz style, publication, and deployment are explicit decisions rather
than hidden defaults.

This parrot (`perroquet`) is source-grounded: it can repeat, explain, quiz,
and route knowledge, but only from material the instructor or content owner has
approved.

<p align="center">
  <img src="images/logo-perroquet.png" alt="MyTeachingPerroquet logo direction" width="360">
</p>

## Who This Is For

This project is meant for people who want a course chatbot, practice quiz tool,
training assistant, documentation companion, or source-grounded Q&A widget but
do not want to become chatbot engineers.

You should be able to use it if you can:

- gather slides, notes, readings, exams, cases, manuals, articles, papers, or
  documentation into a folder;
- answer questions about what belongs in the course and what should stay
  private;
- review generated summaries, exercises, and deployment settings before
  students see them.

You do not need to know how retrieval, vectors, serverless functions, schemas,
or website hosting work. The repository gives the agent the workflow, the
contracts, the checklists, and the stop points.

Although the default language is educational, the pipeline is not limited to
university courses. The same structure can support workshops, corporate
training, onboarding manuals, research-paper companions, policy guides, product
documentation, book notes, and internal knowledge bases.

## What It Builds

A complete run can produce:

- a clean unified course corpus organized by topic and session;
- a human-review packet showing what sources were used and what was excluded;
- a verified quiz bank with question types based on the actual course exams and
  practice material;
- a TA chatbot source tree that answers from the approved corpus;
- an optional quiz mode inside the TA;
- local build reports, privacy notes, cost notes, and deployment notes;
- an optional password-protected preview or production deployment.

The main selling point is not just that it calls an LLM. The TA runtime is
deliberately constrained so it behaves like a small, predictable teaching
interface instead of an open-ended chatbot. The deployed function enforces
short answers, strict prompt policies, source-grounded retrieval, token caps,
rate limits, session limits, password/auth controls, budget tracking, and
degraded modes when spending gets too high.

The raw dump is not the product. The product is the curated corpus plus the
verified questions and solutions. Raw archives, exams, grades, spreadsheets,
answer keys, and private notes stay local unless explicitly approved for a
narrow purpose.

You can also use only one part of the pipeline. For example, you can stop after
Phase 1 if all you need is a clean verified corpus, run only Phase 2 if you
already have approved source material and want a question bank, or run only
Phase 3 if you already have a curated corpus and want a deployable assistant.

## Use The Whole Pipeline Or One Piece

The repo is designed as a set of reusable pipelines, not a single mandatory
path.

| Need | Use | Typical Result |
|---|---|---|
| Clean a messy source folder | Phase 1 corpus prep | Unified corpus, source inventory, quarantine list, review packet |
| Build practice questions | Phase 2 quiz bank | Verified question/solution JSON and catalog |
| Turn approved material into a chatbot | Phase 3 TA ingestion | Chunked/vectorized retrieval corpus and web widget |
| Deploy an existing assistant | Deployment recipe | Preview or production site with auth and env-var checklist |
| Run the whole course workflow | Full pipeline | Corpus, quiz bank, TA system, deployment notes |

This modularity is useful when the source is not a course. A research group may
only want a paper companion. A team may only want a Q&A bot over internal docs.
A teacher may only want a verified set of case-study questions. The same safety
rules apply: inspect sources, define what is allowed, produce artifacts, run
checks, and stop for approval.

## How The Pipeline Works

The workflow has four practical stages.

| Stage | What Happens | What You Review |
|---|---|---|
| Setup | The agent explores the dump and asks an upfront decision packet. | Course identity, product goal, source policy, quiz profile, Phase 3/deployment defaults. |
| Phase 1: Corpus | Approved sources are merged by topic into one course voice. | Unified corpus, source inventory, session map, quarantines, privacy boundaries. |
| Phase 2: Quiz Bank | Exercises are generated, then independently verified. | Smoke sample, full bank, type mix, difficulty, solutions, validation reports. |
| Phase 3: TA | Approved corpus and verified quiz bank are loaded into the TA system. | Preflight, chunking, exercise transform, vector build, access policy. |
| Deployment | Optional preview or production site is deployed. | URL, password/auth, environment variables, residual risks. |

The default is not to split course content by instructor, slide deck, or raw
file. When multiple sources cover the same topic, Phase 1 creates one unified,
source-grounded corpus in a coherent course voice. Provenance and conflicts are
kept in manifests for review.

The default is also not to guess quiz types from the academic discipline. The
agent must inspect real exams, practice questions, cases, graphs, assignments,
and rubrics before proposing the quiz mode. If the course uses yes/no,
multiple-choice, open-ended, and case-study questions, those become the
candidate quiz types.

## Constrained TA Runtime

The `phase3-ta-llm-system` is built to keep the student-facing assistant
bounded, cheap, and reviewable.

| Control | Default Behavior |
|---|---|
| System prompt | `course_ta` answers as a short university TA, cites sources when relevant, hints instead of solving homework, and replies in the student's language. |
| Output cap | `MAX_TOKENS=450`, with prompt-level hard limit around 200 words. |
| Input cap | Student messages are truncated at `MAX_MESSAGE_WORDS=200`. |
| History cap | Only the last few turns are kept, with user and assistant history truncated. |
| Retrieval cap | Retrieved chunks are shrunk before entering the prompt to reduce token use. |
| Formatting policy | No bullets, numbered lists, headings, emojis, or long essay answers in the default TA profile. |
| Auth and sessions | Password/JWT flow, failed-login limits, per-session message limits, and global request-per-minute limits. |
| Budget controls | Daily budget tracking, reduced-token mode, quiz-only mode, and exhausted-budget shutdown. |
| Quiz mode | Many quiz actions, such as next exercise or reveal hint, use local structured data and avoid LLM calls. |

These constraints are why the system is suitable for low-cost teaching use.
The assistant is not allowed to expand indefinitely, ingest arbitrary private
material, or turn every student click into a large model call.

## Quick Start

Clone or open this repository, then place private course material outside git
or under a gitignored local folder:

```text
courses/<course_id>/raw/
```

Start your preferred agent in this folder and say:

```text
Use the full TA plus quizbank pipeline in this repo.
My course material is in courses/<course_id>/raw.
Explore the dump first. Ask the upfront decision packet, then write a
phase-by-phase plan for my approval before producing anything downstream.
```

For a non-course assistant, use the same pattern:

```text
Use the TA ingestion pipeline in this repo.
My approved documentation is in work/my-docs-corpus.
Build a source-grounded assistant for this material, keep private files local,
and ask before any deployment step.
```

In Claude Code, you can also use:

```text
/dump courses/<course_id>/raw
```

The first pass should not generate the final corpus, quiz bank, vectors, or
website. It should inspect the material and ask clear questions. For the full
pipeline, those questions should cover:

- course identity, audience, language, and final product;
- unified topic corpus map and source precedence;
- quarantined/private/source-only material;
- exercise types, counts, quotas, difficulty, and solution style;
- quiz-mode visibility and question-selection behavior;
- generation and verification model roles;
- TA persona, source strictness, and ingestion scope;
- runtime provider, embedding provider, secrets, budget, auth, and deployment
  target;
- branding, naming, copyright, and personal-data exclusions.

You can answer with “keep defaults except ...” when the proposal is mostly
right.

## Output Bundle

A successful run maintains a local course bundle:

```text
courses/<course_id>/
  workflow_config.json
  raw/                         # private source dump, gitignored
  phase1-output/
    human-verification/
    moreexercices-input/
    ta-llm-input/
    APPROVAL.json
  phase2-output/
    smoke/
    full/
  phase3-output/
    ingestion/
    deployment-preview/
    production/
  USER_GUIDE.md
  VERIFICATION.md
  SOURCE_NOTES.md
  ASSESSMENT_STYLE_AUDIT.md
  DEPLOYMENT.md
  PRIVACY.md
  COST_NOTES.md
```

The operational systems are:

- `phase1-corpus-prep/`: source intake, routing, provenance, unified corpus
  rules, and handoff contracts;
- `phase2-quizbank/quiz-llm-bank/`: quiz generation, validation, audit, fixes,
  and catalog production;
- `phase3-ta-llm-system/`: TA retrieval corpus build, quiz transform, vector
  build, web widget, and Netlify deployment.

## Current Status

This repository is ready as an agent-guided workflow scaffold and public
release template. It includes the Phase 2 quizbank engine, the Phase 3 TA
system, approval scaffolding, checklists, templates, and agent instructions.

The fully automatic one-command path is still under development. Until the
generic Phase 1 runner and wrapper drivers are complete, a coding agent should
follow the pipeline recipes and run the phase systems directly, stopping at the
approval files described below.

## Pipeline Recipes

| Goal | Start With | Output | Main Risk To Control |
|---|---|---|---|
| Full course TA plus quizbank | `pipelines/full-course-ta-quizbank.md` | Verified corpus, quiz bank, TA source tree, deployment notes | Source trust, quiz correctness, privacy, cost |
| Phase 1 only | `pipelines/phase1-corpus-prep.md` | Human-verification corpus plus downstream handoffs | Bad material entering generation or TA retrieval |
| Quizbank only | `pipelines/quizbank.md` | Validated exercise JSON and catalog | Scope drift, wrong solutions, weak twins |
| TA ingestion only | `pipelines/ta-ingestion.md` | Chunked/vectorized TA corpus | Leaking exams/corrections into retrieval |
| Netlify deployment | `pipelines/deploy-netlify.md` | Preview or production deployment | Secrets, public exposure, budget |

All public recipes follow `pipelines/PIPELINE_CONTRACT.md`.

## Approval Gates

Automation must stop unless the relevant approval file says
`"status": "approved"`.

| Checkpoint | Approval File | You Verify |
|---|---|---|
| Setup / plan | `courses/<course_id>/APPROVAL.setup.json` | Course identity, decisions, source policy, quiz plan, TA/deployment defaults |
| Phase 1 corpus | `courses/<course_id>/phase1-output/APPROVAL.json` | Inventory, source tiers, session routing, unified topic corpus, quarantines |
| Phase 2 smoke | `courses/<course_id>/phase2-output/smoke/APPROVAL.json` | Sample exercises, style, scope, difficulty, language behavior |
| Phase 2 full | `courses/<course_id>/phase2-output/full/APPROVAL.json` | Validators, audits, fixes, review sample, catalog |
| Phase 3 ingestion | `courses/<course_id>/phase3-output/ingestion/APPROVAL.json` | TA lecture tree, exercise transform, chunk/rebuild/vector reports |
| Preview deployment | `courses/<course_id>/phase3-output/deployment-preview/APPROVAL.json` | Preview URL, access control, env vars, content behavior |
| Production deployment | `courses/<course_id>/phase3-output/production/APPROVAL.json` | Final production deployment approval |

Setup decisions are not deployment approval. Choosing a runtime provider or a
preview target early only records the intended path. Ingestion, preview, and
production still require their own approvals after the artifacts exist.

## Safe Defaults

The workflow starts conservative:

- monolingual unless bilingual output is requested or clearly required;
- approved sources are merged into one unified topic corpus before quiz
  generation or TA retrieval;
- exams, corrections, answer keys, rubrics, and active assessments are
  authoring-only;
- transcripts, AI summaries, noisy notes, spreadsheets, duplicates, grades, and
  personal data are quarantined unless explicitly approved for a narrow use;
- exercise types and quotas are based on inspected assessment evidence;
- Phase 2 smoke generation happens before full quiz generation;
- quiz generation and quiz verification run in separate contexts;
- TA retrieval uses canonical approved corpus by default;
- quiz-visible questions must fit the short-form TA runtime;
- password auth is on by default for deployed course assistants;
- production deployment requires explicit approval.

The deployed `course_ta` is intentionally short-form: about 200 words, 2-3
prose paragraphs, no bullets/lists/headings/emojis, source-grounded, and
hint-oriented rather than homework-solving. Long exam essays or passage
analysis can calibrate private exercise generation, but quiz-visible items
should usually be adapted into short prompts.

## Model And API Choices

Different phases can use different tools and keys.

| Layer | Used For | Default | Credential Path |
|---|---|---|---|
| Agent orchestration | Reading the dump, asking questions, running the workflow | User-selected agent | Claude Desktop, Claude Code, Codex, or another local agent subscription |
| Quiz generation | Producing exercises and solutions in Phase 2 | Claude Opus 4.7 | Agent session/subscription configured in `workflow_config.json` |
| Quiz verification | Independent audit of generated exercises and solutions | Separate fresh Claude Opus 4.7 verifier | Separate fresh agent session; optional secondary verifier |
| TA query LLM | Answering student chat/explain requests in the deployed TA | Mistral Medium via OpenAI-compatible API | `MISTRAL_API_KEY` by default; configurable |
| TA embeddings | Vector build and per-query retrieval embeddings | OpenAI `text-embedding-3-small` | `OPENAI_API_KEY` |

Phase 2 can run through subscription-based AI agents. The deployed TA uses API
keys at runtime: one for embeddings and one for the chat/query model.

Common Phase 3 runtime choices:

| Runtime Choice | Required Settings |
|---|---|
| Mistral default | `OPENAI_API_KEY`, `MISTRAL_API_KEY` |
| Claude runtime | `OPENAI_API_KEY`, `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY` |
| OpenAI runtime | `OPENAI_API_KEY`, `LLM_BASE_URL=https://api.openai.com/v1`, `LLM_API_KEY`, optional `MODEL_ID` |
| Groq runtime | `OPENAI_API_KEY`, `LLM_BASE_URL=https://api.groq.com/openai/v1`, `LLM_API_KEY`, optional `MODEL_ID` |

## Educators Stay In Control

<img src="images/human-control-mascot.png" alt="A frog at a desk with a chalkboard of pseudocode behind him, quietly reviewing the agent's output" align="right" width="260" />

The educator pilot decides:

- which sources are course truth;
- which sources are private, authoring-only, or excluded;
- how topics and sessions should be organized;
- what kinds of questions students should practice;
- whether generated exercises are pedagogically acceptable;
- whether the TA can ingest the approved material;
- whether a preview or production deployment is allowed.

The agent surfaces uncertainty, proposes defaults, writes artifacts, runs
checks, and stops. Missing approval is a blocker, not a warning.

## Privacy Responsibility

Do not publish private course archives, raw dumps, student data, spreadsheets,
answer keys, copyrighted readings, secrets, or deployment credentials. Use
gitignored `courses/`, `work/`, `private_sources/`, or `local_sources/`
folders for private material.

Only the curated, approved corpus and verified exercise/solution JSON should
go online with the bot. Public examples and issues should not contain private
source excerpts or assessment keys.

## Repository Structure

```text
AGENTS.md                    Repo-level instructions for Codex and other agents
CLAUDE.md                    Claude-specific workflow instructions
checklists/                  Human verification checklists
pipelines/                   User-facing pipeline recipes
templates/                   Standard output bundle templates
tools/workflow/              Future orchestration scripts and helper notes
phase1-corpus-prep/          Phase 1 specs, contracts, templates, question bank
phase2-quizbank/             Quizbank generation system
phase3-ta-llm-system/        TA ingestion, widget, and deployment system
```
