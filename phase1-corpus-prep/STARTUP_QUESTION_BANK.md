# Startup Question Bank

Use this after the first exploration of a teaching-material dump. The agent
must inspect the dump first, infer as much as possible, then ask the questions
needed to configure the requested workflow.

This is not a linear interview. It is a bank of targeted questions. Each
question has:

- `Ask when`: the uncertainty trigger after exploration;
- `Question`: the user-facing wording;
- `Default`: what the workflow should assume if the user does not override;
- `Writes`: the config or artifact affected.

For a full TA plus quizbank run, prefer one compact upfront decision packet
after exploration. The packet should group all known non-approval decisions by
phase: Phase 1 corpus, Phase 2 quizbank, Phase 3 TA ingestion/runtime, and
deployment. Approval questions still happen at their phase gates.

## Pre-Question Exploration Report

Before asking anything, produce a short exploration report:

```text
I found:
- likely course: <name/domain/language>
- likely sessions: S1..Sn with titles
- candidate canonical sources: <folders/files>
- candidate authoring-only sources: <exams/corrections/cases>
- quarantine candidates: <transcripts/AI summaries/duplicates/noisy notes>
- detected software/math/graphical components: <tools/methods>
- assessment-style evidence sampled: <exams/cases/questions/figures/readings
  actually opened, not just listed>
- unresolved decisions: <numbered short list>
```

Then ask either the highest-impact unresolved question first or, for a full
pipeline run, the full upfront decision packet.

## Question Selection Rules

- Do not ask for facts already strongly inferred from the dump; present them for confirmation.
- Ask blocking safety questions before style questions.
- Prefer defaults from `pipelines/PIPELINE_CONTRACT.md`,
  `templates/WORKFLOW_CONFIG.template.json`, and this question bank when the
  user is unsure.
- If a question affects TA retrieval safety, treat it as blocking.
- Do not set exercise style, type mix, difficulty, or solution requirements
  from discipline/domain labels alone. First inspect actual assessment and
  practice content and record evidence in `ASSESSMENT_STYLE_AUDIT.md`.
- If exercise-style evidence is incomplete, do not apply the generic
  quantitative/qualitative defaults. Ask which assessment/practice sources
  should drive Phase 2, or mark `exercise_profile.basis` as
  `pending_assessment_style_audit`.
- If a question affects only cost, use the default and record it as adjustable later.
- For full-pipeline runs, ask all known setup decisions upfront when they can
  be answered from exploration: Phase 1 corpus policy, Phase 2 output shape,
  Phase 3 TA runtime/ingestion policy, deployment target, auth, privacy, and
  budget defaults. Do not ask final approval questions upfront; approvals stay
  gated after the relevant artifacts exist.
- Store every answer in `workflow_config.json`, `SOURCE_INVENTORY.md`,
  `SESSION_MAP.md`, source manifests, or `APPROVAL.json`; do not rely on chat history.

## A. Course Identity And Intended Product

### Q-A1: Course Identity Confirmation

Ask when: course name, domain, institution, or term is missing or inferred with low confidence.

Question: "I infer this is `<course/domain>` for `<term/institution>`. What exact course name and term should appear in generated configs and student-facing TA text?"

Default: use syllabus title if present; otherwise use a neutral `example_course_<year>` slug until confirmed.

Writes: `workflow_config.course`, `moreexercices-input/course_config.json`, `ta-llm-input/data/course_config.json`.

### Q-A2: Primary Goal

Ask when: the user has not specified whether they want chat only, quiz only, or both.

Question: "Should the end product be a chat TA only, a quiz bank only, or both chat TA plus quiz mode?"

Default: both, but keep quiz mode disabled until the quiz bank is verified.

Writes: `workflow_config.ta.features.quiz_mode_enabled`, Phase 2 run plan.

### Q-A3: Audience Level

Ask when: course level is unclear from materials.

Question: "Who is the target audience: undergraduate intro, undergraduate advanced, masters/MBA, PhD, executive/professional, or mixed?"

Default: infer from syllabus/course code and use `undergraduate advanced` if unclear.

Writes: `workflow_config.course.audience_level`, prompt persona, difficulty calibration.

## B. Language And Translation Policy

### Q-B1: Primary Language

Ask when: multiple languages are detected or language confidence is mixed.

Question: "The dump appears to contain `<languages>`. Which language should be the primary generation language?"

Default: dominant lecture/source language.

Writes: `workflow_config.course.primary_language`, `course_config.languages[0]`.

### Q-B2: Bilingual Twins

Ask when: bilingual source material exists or the user mentioned multilingual teaching.

Question: "Do you want bilingual twin exercises, or should the first run stay monolingual?"

Default: monolingual unless explicitly requested or the course is clearly bilingual.

Writes: `workflow_config.course.languages`, Phase 2 twin-generation plan.

### Q-B3: Terminology Enforcement

Ask when: bilingual terms, acronyms, or domain translations are detected.

Question: "I found these important term pairs: `<sample>`. Are any translations mandatory or forbidden?"

Default: use extracted glossary with no forbidden translations unless the source explicitly says so.

Writes: `glossary_terms`, `terminology_fr`, bilingual validator inputs.

## C. Session Map And Scope

### Q-C1: Canonical Session Order

Ask when: file numbering, syllabus order, and topic order disagree.

Question: "Should the course follow the syllabus order I inferred, or should any topics be moved to a different session?"

Default: syllabus order if present; otherwise folder/file order after topic normalization.

Writes: `SESSION_MAP.md`, `workflow_config.sessions`, downstream `sessions[]`.

### Q-C2: Session Granularity

Ask when: lectures are too long, merged, or split differently across sources.

Question: "Should these materials be organized by class meeting, by topic module, or by week?"

Default: topic module/session buckets named `S1`, `S2`, ... that match the pedagogical sequence.

Writes: `workflow_config.sessions[].id`, `dir`, lecture output layout.

### Q-C3: Multiple Instructor Variants

Ask when: multiple instructors or source variants cover overlapping material.

Question: "I found overlapping variants from `<sources/instructors>`. I will
merge approved variants into one unified topic corpus by default. Which source
should have precedence if they conflict, and are any variants outdated,
authoring-only, or unsafe for the student-facing corpus?"

Default: build one unified topic corpus per session/topic. Merge approved
variants by topic, write in one course voice, deduplicate overlaps, and keep
provenance/conflicts in manifests. Do not emit raw instructor/source splits to
quiz generation or TA retrieval.

Writes: source routes, `LECTURE_SOURCE_TAGS.md`, unified corpus plan.

### Q-C4: Forward-Reference Boundaries

Ask when: early sessions mention later concepts, or scope terms are hard to assign.

Question: "For these concepts I detected early but likely taught later: `<sample>`. Should they be allowed in early exercises, or treated as later-session forward references?"

Default: treat as later-session concepts unless the syllabus says they are introduced early.

Writes: `scope_terms`, `foundational_terms`, content-boundary config.

### Q-C5: Prerequisites

Ask when: sessions depend on earlier sessions but prerequisites are not explicit.

Question: "Are prerequisites strictly cumulative, or can sessions be treated as mostly independent?"

Default: cumulative in session order.

Writes: `sessions[].prerequisites`, scope resolver inputs.

## D. Source Trust And Routing

### Q-D1: Canonical Sources

Ask when: more than one source type could be used as course truth.

Question: "Which sources should count as canonical course truth for student answers: slides only, slides plus syllabus, slides plus lecture notes, or another set?"

Default: slides plus syllabus; lecture notes only if explicitly instructor-approved.

Writes: source tiers, TA lecture source inclusion.

### Q-D2: Lecture Notes Admission

Ask when: lecture notes are present.

Question: "Should lecture notes be quarantined by default, used only as authoring supplements, or admitted into TA retrieval after review?"

Default: quarantine unless explicitly approved.

Writes: `SUPPLEMENT_SOURCE_MANIFEST.md`, `QUARANTINE_MANIFEST.md`, TA source policy.

### Q-D3: Transcript Admission

Ask when: transcripts/audio-derived text are present.

Question: "Should transcripts remain quarantined, or should I extract targeted excerpts for human review?"

Default: quarantine.

Writes: `QUARANTINE_MANIFEST.md`, optional supplement routes.

### Q-D4: Readings And Cases

Ask when: papers, case studies, readings, news articles, or datasets are found.

Question: "Should readings/cases be used only for exercise authoring, or also included in the student-facing TA corpus?"

Default: authoring-only unless the syllabus marks them as assigned readings.

Writes: source tiers, `SourceExamples`, TA inclusion list.

### Q-D5: Duplicates And Generated Derivatives

Ask when: duplicate folders, exports, AI-enriched summaries, or generated files are found.

Question: "I found likely duplicates/generated derivatives: `<sample>`. Should I ignore these unless a specific file is needed?"

Default: ignore/quarantine duplicates and generated derivatives.

Writes: `SOURCE_INVENTORY.md`, `QUARANTINE_MANIFEST.md`.

## E. Assessment And Authoring Material

### Q-E1: Past Exams Use

Ask when: exams, question pools, assignments, or corrections are present.

Question: "May I use past exams and question pools as private authoring examples for quiz generation?"

Default: yes for authoring, never for TA lecture retrieval.

Writes: `ASSESSMENT_SOURCE_MANIFEST.md`, `moreexercices-input/inbox/ExamExamples`.

### Q-E2: Corrections And Answer Keys

Ask when: corrections, answer keys, solutions, or grading rubrics are present.

Question: "May I use corrections/answer keys privately to calibrate solutions, while excluding them from student-facing TA retrieval?"

Default: yes, authoring-only.

Writes: `ASSESSMENT_SOURCE_MANIFEST.md`, authoring-only tags.

### Q-E3: Reuse Sensitivity

Ask when: assessment material appears recent, reusable, or confidential.

Question: "Are any exams or questions still active/reusable and therefore too sensitive to include even as authoring examples?"

Default: include only older or explicitly approved assessment material.

Writes: `ASSESSMENT_SOURCE_MANIFEST.md`, quarantine routes.

## F. Exercise Profile

### Q-F0: Assessment-Style Evidence Gate

Ask when: Phase 2 quizbank generation is requested, or when the user asks for
the full TA plus quizbank pipeline, and the agent has not yet inspected actual
assessment/practice content.

Question: "Before choosing exercise types, I need to mirror how this course
actually assesses students. I have inspected `<sampled paths>` and observed
`<question styles>`. Should this evidence drive the smoke quizbank, or are
there other exams, assignments, cases, figures, or practice questions I should
inspect first?"

Default: infer the candidate exercise types from representative
assessment/practice material, then ask the user to confirm or override. No
exercise-profile default is allowed until representative assessment/practice
material has been inspected. Use `pending_assessment_style_audit` in
`workflow_config.exercise_profile.basis` if evidence is incomplete.

Writes: `ASSESSMENT_STYLE_AUDIT.md`,
`workflow_config.exercise_profile.basis`,
`workflow_config.exercise_profile.assessment_style_evidence`.

### Q-F1: Exercise Mode

Ask when: the course could support several exercise styles and Q-F0 has
evidence from actual assessment/practice content.

Question: "Based on the assessment/practice evidence I inspected (`<short
evidence summary>`), should the quiz bank emphasize open written questions,
graphical/diagram analysis, case applications, source analysis, conceptual
checks, true/false, interpretation, calculations, software output, or a mix?"

Default: mirror the observed assessment style. Do not use the generic
quantitative/qualitative profile if exams or practice material show a different
pattern. If the bank will feed the deployed TA quiz mode, adapt long
exam-style essays or passage analysis into short case/application prompts
rather than making long text-analysis items visible in the chatbot.

Writes: `exercise_types`, `type_distribution`, `ASSESSMENT_STYLE_AUDIT.md`.

### Q-F1a: Exercise Type Inference

Ask when: the evidence shows recognizable question formats.

Question: "From the sampled exams and practice material, I infer these quiz
types and approximate weights: `<types and weights>`. Do you approve this
exercise-type profile for quiz mode, or should I add/remove/reweight types?"

Default: propose types from the observed evidence, not from the course domain.
Common inferred quiz-mode types include:

- `YES_NO`: yes/no, true/false, justify briefly;
- `MCQ`: multiple-choice with distractor explanations;
- `OPEN`: short open-ended conceptual or explanation question;
- `CASE`: short case/application question;
- `GRAPHICAL`: diagram/graph interpretation when figures are central;
- `CALCULATION`: numerical question only when calculations are actually central;
- `SOURCE_ANALYSIS`: short reading/source interpretation when this appears in
  assessment and fits quiz mode.

If the evidence looks like DDRS-style exams with yes/no, open-ended,
multiple-choice, and case-study questions, infer those types directly and
propose them. Do not collapse them into generic math/concept defaults.

Writes: `exercise_types`, `type_distribution`,
`question_type_labels`, `ASSESSMENT_STYLE_AUDIT.md`.

### Q-F1b: TA Quiz-Mode Suitability

Ask when: the quizbank will be copied into the deployed TA or quiz mode is
requested.

Question: "The TA runtime is short-form by design: about 200 words, 2-3 prose
paragraphs, no bullets/lists/headings/emojis, and hints rather than full
homework solutions. Which generated question types should be visible in quiz
mode, and which long-form assessment styles should remain authoring-only or be
converted into short case/application questions?"

Default: quiz-visible exercises must fit short chat turns. Convert long
passage/text-analysis or essay prompts into short case/application questions,
or hide them from quiz mode. Keep full exam-style rubrics private unless the
user explicitly wants a separate long-form assessment bank.

Writes: `exercise_profile.quiz_visible_types`,
`exercise_profile.hidden_from_quiz`, `ta.hidden_question_types`,
`ASSESSMENT_STYLE_AUDIT.md`.

### Q-F2: Phase 2 Output Size

Ask when: Phase 2 quizbank generation is requested and no explicit smoke/full
target size is recorded.

Question: "Before Stage 2/Phase 2 generation, please confirm the output size:
how many exercises per session per language for the smoke run, how many for
the full run, and whether any sessions should have a different count?"

Default: smoke run 10 exercises per session per language; full run 30
exercises per session per language; counts apply to every approved session
unless the user gives per-session overrides. The smoke run should include at
least one example of each enabled quiz-visible type when feasible.

Writes: `exercise_profile.smoke_exercises_per_session`,
`exercise_profile.full_exercises_per_session`,
`batch_size`, `generation_loops`, `sessions[].exercise_count`,
`sessions[].exercise_count_overrides`.

### Q-F2b: Per-Type Exercise Mix

Ask when: more than one exercise type is enabled, when Phase 2 generation is
requested, or when the user asks for a specific bank shape.

Question: "Before Stage 2/Phase 2 generation, please confirm the exact exercise
types and quotas. I infer `<exercise_types>` from the evidence. For each
session, should I use this distribution: `<type_distribution>`, or set exact
quotas such as 8 open-ended, 8 case, 6 multiple-choice, 4 yes/no, and 4
graphical out of 30? Which of these types should be visible in quiz mode?"

Default: distribute enabled types according to the assessment-style audit. If
the audit shows mostly open questions, cases, graphical analysis, or very few
calculations, reflect that even when the course domain is quantitative. If the
audit is incomplete, do not set exact quotas yet. The sum of each
`type_distribution` must equal `sessions[].exercise_count`.

Writes: `exercise_profile.exercise_types`,
`exercise_profile.type_distribution`, `exercise_profile.quiz_visible_types`,
`exercise_profile.hidden_from_quiz`,
`sessions[].type_distribution_overrides`.

### Q-F3: Difficulty Target

Ask when: audience level, grading rigor, or assessment difficulty is unclear
after inspecting representative assessment/practice material.

Question: "Should exercises skew easy for practice, balanced, or harder for exam preparation?"

Default: balanced: `EASY 30%`, `MED 45%`, `HARD 25%`.

Writes: `difficulty_distribution`.

### Q-F4: Solution Style

Ask when: solution verbosity or pedagogy is unclear.

Question: "Should solutions be concise answer keys, step-by-step academic explanations, or hints before the final answer?"

Default: concise teaching explanation plus 2-3 progressive hints.

Writes: `solution_constraints`, prompt profile.

### Q-F5: Per-Type Solution Requirements

Ask when: enabled exercise types need different solution artifacts.

Question: "Do any question types need special solution requirements, such as
grading rubrics for open questions, figure/graph interpretation criteria,
source citations for case/source-analysis questions, formulas for calculations,
or code blocks for software?"

Default: every exercise has `solution.text`, `solution.key_formula` when
applicable, `solution.numerical_answer` when applicable, 2-3 hints, and
`common_mistakes` or rubric notes for computation, interpretation,
graphical-analysis, open-question, or case questions. Software questions
include `software_code` when code is part of the expected answer.

Writes: `exercise_profile.solution_requirements_by_type`,
Phase 2 schema/prompt settings, TA transform compatibility notes.

### Q-F6: Quiz Mode Question Selection

Ask when: quiz mode is requested or a verified quiz bank will be copied into
the TA.

Question: "In quiz mode, should students choose question type before practice, see an All option, and receive random questions, or should the quiz follow a fixed session order?"

Default: students choose session, then question type; include an `All` option;
serve random approved exercises within the selected session/type; preserve the
selected type when the student asks for the next question.

Writes: `ta.features.quiz_mode_enabled`, `ta.hidden_question_types`,
`ta.question_type_labels`, quiz-mode review checklist.

## G. Math, Graphs, Software, And Data

### Q-G1: Math Validation

Ask when: formulas, calculations, statistics, economics, finance, physics, or engineering content is detected.

Question: "Should numerical/math exercises be generated and automatically checked, or should the first run avoid calculations?"

Default: enable math exercises when calculations are central to the course; otherwise avoid them in smoke run.

Writes: `exercise_types`, `math_validation.checks`.

### Q-G2: Graphical Analysis

Ask when: slides contain diagrams, charts, supply/demand graphs, model figures, or visual interpretation.

Question: "Should the quiz bank include graphical/diagram analysis questions?"

Default: include only if figures can be represented textually or validated by a course-specific guide.

Writes: exercise types, graphical guidance, downstream change requests if validators are missing.

### Q-G3: Software Tool

Ask when: code, commands, notebooks, spreadsheets, or software output is detected.

Question: "I detected `<tool>`. Should the bank include software-output/code questions, and should they be visible in student quiz mode?"

Default: include `SOFTWARE` only if software is part of assessment; hide from quiz mode if not student-facing.

Writes: `software_tool`, `exercise_types`, TA `hidden_question_types`.

### Q-G4: Datasets

Ask when: CSV, Excel, Stata, R, notebooks, or data folders are present.

Default: quarantine Excel workbooks (`.xls`, `.xlsx`, `.xlsm`) because they
often contain grades, rosters, exports, or private assessment data. Admit a
spreadsheet only after the user confirms it is a course dataset and names the
allowed downstream use.

Question: "Are datasets meant for student exercises, instructor authoring examples, or not part of this workflow?"

Default: authoring examples unless explicitly assigned to students.

Writes: source tier, exercise prompt references, TA inclusion policy.

## H. TA Behavior And Deployment

### Q-H0a: Generation And Verification Agents

Ask when: Phase 2 quizbank generation is requested and model/provider choices
are not already specified.

Question: "Should Phase 2 use the default setup: Claude generates the exercises, then a separate fresh Claude verifier audits them? Or do you want a different verifier model added?"

Default: use the same model family by default, but with role separation:
one fresh generation context and one fresh verification context. Add Codex or
another verifier only if requested or already available.

Writes: `workflow_config.llm.generation`, `workflow_config.llm.verifiers`,
`workflow_config.llm.verification_policy`.

### Q-H0: Branding And Visual Defaults

Ask when: any student-facing HTML, widget, dashboard, review packet, or deployable page will be generated.

Question: "Should I use the default academic palette and styling, or do you have course/institution branding colors, logos, typography, or footer text to use?"

Default: use the Flying Mermoz-style academic defaults: deep navy, accent blue, teal, light blue, white, and neutral grays. Do not add logos unless provided.

Writes: `workflow_config.branding`, TA widget setup inputs, generated docs/templates.

### Q-H0b: TA Persona

Ask when: TA deployment or student-facing exercise feedback is requested.

Question: "The TA LLM system default is `course_ta`: a university-level
teaching assistant with a hard short-form runtime shape, about 200 words, 2-3
prose paragraphs, no bullets/lists/headings/emojis, replies in the student's
language, cites course sources when relevant, and gives hints rather than
solving homework. Do you want to keep this default, or add a one-time persona
addendum such as warmer tutor, more casual explainer, stricter exam-prep coach,
or concise technical assistant?"

Default: keep the TA LLM system default with no `assistant_persona` addendum.
This is a one-time config choice stored in the TA prompt/persona and can be
changed later by editing `ta.assistant_persona` or `prompt_profile`.

Writes: `ta.assistant_persona`, prompt profile, solution style.

### Q-H1: TA Source Strictness

Ask when: supplements/readings/cases could enter TA retrieval.

Question: "Should the TA answer only from canonical lectures, or also from approved supplements/readings?"

Default: canonical lectures only for first build.

Writes: TA source inclusion list.

### Q-H2: Auth And Privacy

Ask when: deployment is requested or material is private.

Question: "Should the deployed TA require a password, and is the content safe to host on Netlify with API-backed LLM calls?"

Default: password required.

Writes: TA `features.auth_required`, deployment checklist.

### Q-H3: Deployment Timing

Ask when: local build succeeds or user requests publishing.

Question: "After local validation passes, should I stop at a preview deploy or proceed to production deployment?"

Default: stop at preview or local build until explicit production approval.

Writes: deployment approval artifact.

### Q-H4: Phase 3 Runtime Provider

Ask when: TA deployment, preview, or local TA runtime testing is requested and
runtime provider choices are not already specified.

Question: "For the deployed TA runtime, should I use the default Mistral chat
model plus OpenAI embeddings, or another runtime provider such as Claude,
OpenAI, Groq, or a compatible OpenAI-style endpoint?"

Default: Mistral chat/query model (`mistral-medium-latest`) plus OpenAI
`text-embedding-3-small` embeddings.

Writes: `ta.runtime.provider`, `ta.runtime.model`,
`ta.runtime.embedding_provider`, `DEPLOYMENT.md`, `COST_NOTES.md`.

### Q-H5: Phase 3 Ingestion Scope

Ask when: TA ingestion will eventually run and corpus/exercise inclusion needs
to be decided before setup.

Question: "When Phase 3 runs, should the TA ingest only the unified canonical
corpus plus the verified quizbank, or should any approved supplements/readings
also enter retrieval?"

Default: ingest the unified canonical corpus and verified exercise bank only.
Supplements/readings stay out of retrieval unless explicitly approved.

Writes: `ta.ingestion_scope`, TA source inclusion list,
`phase3-output/ingestion` plan.

### Q-H6: Deployment Target And Access

Ask when: the user wants a deployable TA or when the final target is unclear.

Question: "Should the final TA stay local-only, stop at a password-protected
preview, or target production deployment later? If deploying, do you already
have a Netlify site name/domain and allowed origin?"

Default: local build plus optional password-protected preview; production only
after a separate explicit production approval. `ALLOWED_ORIGIN` is restricted
to the preview/production site when known.

Writes: `deployment.target`, `deployment.netlify_site`,
`deployment.allowed_origin`, `ta.features.auth_required`, `DEPLOYMENT.md`.

### Q-H7: Runtime Budget And Secrets

Ask when: deployment or vector building is requested.

Question: "Do you want the default budget-conscious runtime settings, and will
the required secrets be provided later (`OPENAI_API_KEY`, runtime LLM key,
`JWT_SECRET`, and optional `TA_CHAT_PASSWORD`)?"

Default: budget-conscious runtime, password required, no secrets committed, and
deployment blocked until required environment variables are confirmed.

Writes: `COST_NOTES.md`, `PRIVACY.md`, `DEPLOYMENT.md`, environment variable
checklist.

## I. Rights, Privacy, And Exclusions

### Q-I1: Copyright/Permission Boundary

Ask when: third-party books, publisher PDFs, news articles, copyrighted cases, or paywalled content are present.

Question: "Do you have permission to process and deploy these third-party materials, or should I keep them authoring-only/private or exclude them?"

Default: do not put third-party copyrighted material into public TA retrieval unless explicitly approved.

Writes: source tiers, deployment risk notes.

### Q-I2: Personal Or Sensitive Data

Ask when: student names, grades, emails, rosters, comments, or identifiable data appear.

Question: "I found possible personal/sensitive data in `<sample path>`. Should I exclude it entirely?"

Default: exclude and quarantine.

Writes: `QUARANTINE_MANIFEST.md`, source inventory.

### Q-I3: Public Naming

Ask when: course/institution/instructor names appear and output may be published.

Question: "Should generated examples and deployment text use real course/institution names or neutral public names?"

Default: real names for private deployment; neutral names for public examples.

Writes: course metadata, TA persona, public docs.

## J. Approval Gates

### Q-J0: Setup Approval

Ask when: the exploration report, startup answers, workflow config, and phase
plan are ready.

Question: "Do you approve this workflow config and phase plan for Phase 1 corpus prep, or should I change source policy, sessions, exercise defaults, model choices, or branding first?"

Default: no approval until explicitly stated.

Writes: `courses/<course_id>/APPROVAL.setup.json` with `"phase": "setup"`.

### Q-J1: Phase 1 Approval

Ask when: Phase 1 artifacts are ready.

Question: "Do you approve this corpus routing for smoke quiz generation, or should any sources/sessions be changed first?"

Default: no approval until explicitly stated.

Writes: `courses/<course_id>/phase1-output/APPROVAL.json` with
`"phase": "phase1"`.

### Q-J2: Smoke Quizbank Approval

Ask when: smoke quizbank generation, validation, audit, and sample review are
ready.

Question: "Do you approve the smoke quizbank style, type mix, difficulty, language behavior, and solution format for full generation?"

Default: no.

Writes: `courses/<course_id>/phase2-output/smoke/APPROVAL.json` with
`"phase": "phase2-smoke"`.

### Q-J3: Full Quizbank Approval

Ask when: smoke generation has been reviewed.

Question: "Do you approve running the full quizbank generation with these settings?"

Default: no.

Writes: `courses/<course_id>/phase2-output/full/APPROVAL.json` with
`"phase": "phase2-full"`.

### Q-J4: TA Ingestion Approval

Ask when: verified quizbank exists and TA copy is proposed.

Question: "Do you approve copying the approved lectures and verified exercises into `ta-llm-system`?"

Default: no.

Writes: `courses/<course_id>/phase3-output/ingestion/APPROVAL.json` with
`"phase": "phase3-ingestion"`.

### Q-J5: Preview Deployment Approval

Ask when: local TA ingestion/build has passed and a preview deployment is
requested.

Question: "Do you approve deploying a preview for testing, with the stated access policy, environment variables, and budget settings?"

Default: no.

Writes:
`courses/<course_id>/phase3-output/deployment-preview/APPROVAL.json` with
`"phase": "deployment-preview"`.

### Q-J6: Production Deployment Approval

Ask when: TA build and preview deploy pass.

Question: "Do you approve production deployment?"

Default: no.

Writes: `courses/<course_id>/phase3-output/production/APPROVAL.json` with
`"phase": "production"`.

## Upfront Question Sets

### Minimal First-Turn Question Set

Use this when the user asked for Phase 1 only, quizbank only, or a narrow task:

1. Confirm course identity and intended product.
2. Confirm session map if inferred with less than high confidence.
3. Confirm canonical vs quarantined source classes.
4. Confirm language/twin policy.
5. Confirm exercise profile and smoke-run size if Phase 2 is in scope.

Everything else should be asked only if the dump creates a specific ambiguity.

### Full-Pipeline Upfront Decision Packet

Use this when the user asks for the complete corpus -> quizbank -> TA workflow
or says they want all questions at the beginning. Keep it compact, pre-filled
from exploration, and let the user answer "keep defaults except ...".

Ask for these decisions upfront:

1. Course identity, audience, language, and final product.
2. Unified topic corpus map, source precedence, quarantines, and supplements.
3. Phase 2 exercise profile: enabled exercise types, smoke/full counts,
   per-type quotas, difficulty, solution style, and quiz-visible types.
4. Phase 2 model roles: generator, fresh-context verifier, optional secondary
   verifier.
5. Phase 3 TA behavior: persona, source strictness, quiz-mode selection UX,
   and ingestion scope.
6. Phase 3 runtime: chat provider/model, embedding provider, expected secrets,
   and budget defaults.
7. Deployment: local-only, password preview, or later production target;
   Netlify site/domain/allowed origin if known.
8. Branding, public naming, copyright boundary, personal-data exclusions, and
   auth/privacy policy.

Do not ask for phase approvals in this packet. Setup approval authorizes Phase
1 only. Phase 1, Phase 2 smoke, Phase 2 full, Phase 3 ingestion, preview, and
production approvals still happen at their gates after artifacts exist.
