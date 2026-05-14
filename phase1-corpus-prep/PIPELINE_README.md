# Phase 1 Pipeline: Dump My Material

This is the first phase of the workflow. Its purpose is to accept a messy dump
of course material and turn it into a verified, human-readable corpus plus
machine-readable handoff packages for downstream systems.

Phase 1 is not the exercise-generation pipeline and it is not TA deployment. It
feeds those workflows.

## Boundary

Phase 1 starts with raw course material:

- slides, notes, syllabi, readings, cases, transcripts, exams, corrections;
- multiple instructor/source variants for the same topic;
- external tools, images, figures, and generated artifacts when explicitly
  provided.

Phase 1 ends with:

- a human-verification corpus in Markdown;
- a `moreexercices` / `quiz-llm-bank` authoring package;
- a `ta-llm-system` source package;
- manifests, provenance, quarantine decisions, and preflight reports;
- deferred downstream change requests, if Phase 1 discovers that later systems
  need alignment.

Phase 1 does not:

- generate the final exercise bank;
- run full `moreexercices` generation loops;
- ingest into `ta-llm-system`;
- build embeddings or deploy the TA;
- modify downstream repos during intake/routing.

## Operating Principle

The pipeline separates three things that are easy to confuse:

1. Source truth: instructor/course material that can be cited as course content.
2. Authoring material: exams, corrections, cases, and examples used to calibrate
   exercise generation.
3. Generated scaffold: helper prompts, seeds, or guides created to steer later
   generation, never treated as course evidence.

Every emitted file must make that distinction visible.

Student-facing lecture output follows an additional rule: raw instructor/source
variants are converted into one unified topic corpus before they enter
downstream lecture trees. The student-facing files should not expose parallel
"instructor A vs. instructor B" lecture streams. Provenance for the raw sources
stays in manifests and human-verification files.

## Phase 1 Stages

1. Intake raw dump and record source paths.
2. Inventory files, duplicates, file types, owners, languages, and obvious risk.
3. Convert usable sources to Markdown while preserving provenance.
4. Classify sources as `canonical`, `supplement`, `assessment_style`,
   `case_source`, `quarantine`, or `generated_scaffold`.
5. Build a topic/session map from the syllabus or instructor-approved structure.
6. Route files and slices by topic, not by misleading source numbering.
7. Extract assessment examples for authoring calibration.
8. Build one clean unified topic corpus per session/topic bucket.
9. Emit the human-readable verification corpus.
10. Emit the `moreexercices-input` package.
11. Emit the `ta-llm-input` package.
12. Run preflight checks and independent Claude/Codex audits.
13. Stop at the Phase 1 workflow-alignment checkpoint.

## Outputs

```text
phase1-output/
  human-verification/
    README.md
    ALL_CORPUS.md
    sessions/S1_*.md
    manifests/*.md
    HUMAN_APPROVAL.md  # optional readable notes
  APPROVAL.json        # machine gate: phase=phase1
  moreexercices-input/
    course_config.json
    inbox/
      Slides/
      ExamExamples/
      SourceExamples/
      LectureNoteSupplements/
      ClaudeSeeds/
      AuthoringGuides/
      Syllabus/
  ta-llm-input/
    data/course_config.json
    sources/
      SOURCES.md
      lectures/
        S1/lecture_S1_topics_merged.md
        S2/lecture_S2_topics_merged.md
      exercises/
  PREFLIGHT_REPORT.md
  DOWNSTREAM_CHANGE_REQUESTS.md
```

## `moreexercices` Connection

`moreexercices-input` is an authoring package. It may contain canonical
materials plus authoring-only material such as exams, corrections, cases, and
targeted supplements. These files are used to design exercise types and calibrate
style, but the final exercise bank is generated later.

`inbox/Slides` should contain the same clean unified topic corpus files used as
the course content boundary for TA, unless a course has an explicit reason to
emit a different authoring-only lecture view. Raw source splits belong in
manifests or human-verification artifacts, not in the default `Slides` content
boundary.

The package must be readable by `quiz-llm-bank` without requiring hidden manual
context. If Phase 1 discovers that `quiz-llm-bank` needs a new validator,
question type, metadata field, or graphical-analysis rule, that need is recorded
in `DOWNSTREAM_CHANGE_REQUESTS.md` and left for the final alignment checkpoint.

Only `Slides/<session.id or session.dir>` and `ExamExamples/<session.id>` are
auto-discovered by the current `quiz-llm-bank` renderer. Any other authoring
folder must be referenced explicitly through `session.inbox_files` or
`session.example_files` in the emitted `course_config.json`.

## `ta-llm-system` Connection

`ta-llm-input` is a student-facing retrieval package. By default, it receives
only approved canonical lecture/source material after unified topic merging.
Exams, corrections, prompts, authoring guides, generated scaffolds, and raw
instructor/source split files must not enter `ta-llm-input/sources/lectures`.

Default lecture layout:

```text
ta-llm-input/sources/lectures/
  S1/lecture_S1_topics_merged.md
  S2/lecture_S2_topics_merged.md
```

Unified corpus files should use normalized topic headings, one coherent
course-level voice, and no source/instructor labels in student-facing headings.
Source provenance is recorded in `SOURCE_INVENTORY.md`,
`LECTURE_SOURCE_TAGS.md`, and `SOURCES.md`.

Exercises in `ta-llm-input/sources/exercises` are empty by default in Phase 1.
Do not emit synthetic placeholder exercises as TA content. Copy the verified
generated exercise bank only after `moreexercices` completes and human review
approves it.

## Deferred Downstream Changes

Phase 1 may reveal that the later workflow needs changes. Examples:

- a new exercise type is needed for this course;
- graphical-analysis validation needs a course-specific rule;
- TA chunking needs additional heading metadata;
- course config schemas need a field that Phase 1 can produce;
- bilingual defaults do not fit the course.

Those are not patched during Phase 1. They are recorded with evidence in
`DOWNSTREAM_CHANGE_REQUESTS.md`. At the final Phase 1 checkpoint, the operator
decides which downstream changes should be implemented before running
`moreexercices` or TA ingestion.

## Definition Of Done

Phase 1 is ready when:

- all raw sources are inventoried or explicitly ignored with a reason;
- all routed content has visible provenance and source-tier tags;
- student-facing lecture files are unified by topic rather than split by raw
  source/instructor;
- session/topic assignment has been human-reviewed;
- authoring-only material is blocked from TA lecture output;
- `moreexercices-input/course_config.json` resolves all referenced files;
- `ta-llm-input/data/course_config.json` and `sources/` pass preflight checks;
- preflight/chunk checks are dry-runs over emitted Phase 1 output, not live TA
  ingestion;
- `APPROVAL.json` records the machine-readable gate status;
- `human-verification/HUMAN_APPROVAL.md` records optional readable notes or
  requested fixes;
- `DOWNSTREAM_CHANGE_REQUESTS.md` records all required later-system changes.
