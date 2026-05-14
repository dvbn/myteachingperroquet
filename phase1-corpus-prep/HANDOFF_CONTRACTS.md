# Handoff Contracts

Phase 1 must serve two consumers without letting their needs contaminate each
other.

## Contract A: `moreexercices` / `quiz-llm-bank`

Purpose: generate and validate the final exercise bank.

Required output:

```text
moreexercices-input/
  course_config.json
  inbox/
    Slides/<session.dir>/lecture_<session.id>_topics_merged.md
    ...
    ExamExamples/<session.id>/*.md
    SourceExamples/<session.dir>/*.md
    LectureNoteSupplements/<session.dir>/*.md
    ClaudeSeeds/<session.dir>/*.md
    AuthoringGuides/*.md
    Syllabus/outline.md
```

Current `quiz-llm-bank` behavior:

- `inbox/Slides/<session.id>/*.md` or `inbox/Slides/<session.dir>/*.md` is
  auto-read as lecture/content-boundary material when `session.inbox_files` is
  absent.
- `inbox/ExamExamples/<session.id>/*.md` is auto-read as assessment-style
  material when `session.example_files` is absent.
- `SourceExamples`, `LectureNoteSupplements`, `ClaudeSeeds`, `AuthoringGuides`,
  and `Syllabus` are organizational folders only unless their files are
  explicitly referenced from `session.example_files` or `session.inbox_files`.

Phase 1 must therefore emit explicit `example_files` or `inbox_files` entries
for any non-auto-discovered authoring material. If broad auto-discovery is
needed later, record it in `DOWNSTREAM_CHANGE_REQUESTS.md` instead of assuming
it exists.

Phase 1 default for `inbox/Slides` is one unified topic corpus file per
session. Raw source/instructor splits are not the default content boundary for
generation because they create duplicated context and make later behavior
harder to audit. If a course needs raw split files for authoring, put them
under a clearly named authoring-only folder and reference them explicitly from
`example_files`, not from the default slide inbox.

Required `course_config.json` fields:

- `course_id`
- `languages`
- `batch_size`
- `generation_loops`
- `llm.generation`
- `llm.verifiers`
- `sessions[]`
- `exercise_types`
- `difficulty_distribution`
- `id_regex`
- `solution_constraints`
- `math_validation`
- `pipeline`
- `foundational_terms`
- `topic_aliases`

Optional but commonly useful fields:

- `course_name_fr` / `course_name_en`
- `institution`
- `domain`
- `software_tool`
- `interpretation_template_fr` / `interpretation_template_en`
- `glossary_terms`
- `content_boundary`
- `scaling`

Per-session required fields:

- `id`
- `dir`
- `title_<language>` for every configured language;
- `topics`
- `scope_terms.{lang}`
- `prerequisites`
- `exercise_count`
- `type_distribution`

Per-session optional fields:

- `inbox_files`, required when lecture/source material lives outside the
  auto-discovered `inbox/Slides/<session.id>` or `inbox/Slides/<session.dir>`
  locations;
- `example_files`, required when assessment or authoring examples live outside
  the auto-discovered `inbox/ExamExamples/<session.id>` location.

Authoring-only materials are allowed here if tagged:

- past exams and question pools;
- corrections and answer keys, when useful for calibration;
- selected cases/readings;
- generated question seeds;
- quarantine-admitted lecture-note excerpts.

## Contract B: `ta-llm-system`

Purpose: build the student-facing TA retrieval corpus and optional quiz mode.

Required output:

```text
ta-llm-input/
  data/
    course_config.json
  sources/
    SOURCES.md
    lectures/
      S1/lecture_S1_topics_merged.md
      S2/lecture_S2_topics_merged.md
    exercises/                     # empty in Phase 1 unless verified bank exists
      <session_dir>/exercises_FR.json
      <session_dir>/exercises_EN.json
```

Lecture contract:

- plain Markdown;
- organized under `sources/lectures/S{n}/`;
- one unified topic corpus file per session by default;
- no student-facing split by instructor, raw deck, or source variant;
- no exam corrections, answer keys, prompt scaffolding, or authoring-only
  material;
- no raw dumps or spreadsheets;
- headings should be meaningful because the TA chunker splits by headings;
- source filenames should avoid `solution`, `correction`, `exercise`,
  `problem`, `case`, and similar preflight-triggering labels unless the file is
  intentionally not a lecture.
- source provenance must be available through manifests such as
  `LECTURE_SOURCE_TAGS.md` and `SOURCES.md`, not through duplicated
  student-facing source streams.

Exercise contract:

- exercises are empty by default at Phase 1;
- Phase 1 should not emit synthetic placeholder exercises as TA content;
- after `moreexercices` generation and verification, final
  `exercises_<LANG>.json` files are copied into this tree;
- solutions are allowed inside exercise JSON for quiz mode, but never inside
  lecture Markdown.
- quiz-visible exercises should fit the TA's short conversational runtime.
  Long essay, long passage-analysis, or rubric-heavy assessment items should
  be shortened into case/application quiz prompts or listed in
  `hidden_question_types`.

Config contract:

`ta-llm-system/data/course_config.json` follows
`ta-llm-system/schema/course_config_schema.json` and may include:

- `course_topics`
- `question_type_labels`
- `hidden_question_types`
- `features.quiz_mode_enabled`
- `features.auth_required`
- `prompt_profile`
- `assistant_persona`
- `terminology_fr`
- `abbreviations`
- `academic_signals`

`course_topics` should be derived from the approved Phase 1 session map, not
maintained as a second source of truth.

## Shared Manifests

Both consumers must be traceable back to the same Phase 1 manifests:

- `SOURCE_INVENTORY.md`
- `SESSION_MAP.md`
- `LECTURE_SOURCE_TAGS.md`
- `ASSESSMENT_SOURCE_MANIFEST.md`
- `SUPPLEMENT_SOURCE_MANIFEST.md`
- `QUARANTINE_MANIFEST.md`
- `APPROVAL.json`
- `DOWNSTREAM_CHANGE_REQUESTS.md`
- `PREFLIGHT_REPORT.md`

`human-verification/HUMAN_APPROVAL.md` may be emitted as readable review notes,
but the machine gate is `phase1-output/APPROVAL.json` with `"phase": "phase1"`.

## Handoff Rule

If a source is not approved for TA retrieval, it may still be present in
`moreexercices-input` for authoring, but it must carry `authoring_only:true` and
must not be copied into `ta-llm-input/sources/lectures`.

If multiple approved raw sources cover the same session or topic, Phase 1
merges them into the session's unified topic corpus before emitting downstream
lecture files. The merge must be deterministic and source-grounded: organize
approved slices by normalized topic, deduplicate overlaps, write in one
pedagogical course voice, record source precedence/conflicts, and record all raw
provenance in the manifests. Do not emit parallel instructor/source streams to
quiz generation or TA retrieval.

## Deferred Change Rule

Phase 1 may discover that a downstream consumer needs a change, but it must not
patch `quiz-llm-bank` or `ta-llm-system` during source intake/routing. Instead,
it records the issue in `DOWNSTREAM_CHANGE_REQUESTS.md` with:

- affected consumer;
- blocking status;
- evidence from Phase 1 artifacts;
- proposed downstream change;
- temporary Phase 1 workaround.

Those changes are reviewed at the final Phase 1 workflow-alignment checkpoint.
