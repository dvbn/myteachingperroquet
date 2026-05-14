# Phase 1 Corpus Prep

This folder defines a reusable first phase for any course-material dump. The
dedicated pipeline readme is
[PIPELINE_README.md](PIPELINE_README.md).

Phase 1 does not generate the final exercise bank. Its job is to turn messy
teaching material into:

- a human-verifiable corpus organized by session/topic;
- a `moreexercices` / `quiz-llm-bank` input package;
- a `ta-llm-system` lecture-source package;
- provenance, quarantine, and approval manifests that prevent bad material from
  flowing downstream silently.

The default lecture handoff is a unified topic corpus. Multiple raw sources or
instructor variants may feed the same session, but the downstream lecture files
should be clean source-grounded readings in one course voice by session/topic,
not parallel source-specific streams.

Phase 1 may identify required changes to `quiz-llm-bank` or `ta-llm-system`,
but those are recorded as deferred downstream change requests. They are not
implemented while intake/routing is still in progress.

## Downstream Contract

Phase 1 produces two synchronized handoffs:

```text
phase1-output/
  human-verification/
  moreexercices-input/
    course_config.json
    inbox/
      Slides/<session.dir>/lecture_<session.id>_topics_merged.md
      ExamExamples/<session.id>/*.md
      SourceExamples/<session.dir>/*.md
      LectureNoteSupplements/<session.dir>/*.md
      ClaudeSeeds/<session.dir>/*.md
      AuthoringGuides/*.md
      Syllabus/outline.md
  ta-llm-input/
    data/course_config.json
    sources/
      SOURCES.md
      lectures/S1/lecture_S1_topics_merged.md
      exercises/  # empty until verified generated bank exists
```

`moreexercices-input` is for exercise generation. Its `Slides` folder should
contain the unified topic corpus as the content boundary. It may also contain
authoring-only materials such as past exams, corrections, selected cases, and
quarantined supplements outside the default slide boundary.

Only `Slides` and `ExamExamples` are auto-discovered by the current
`quiz-llm-bank` renderer. Other authoring folders must be referenced explicitly
in the emitted session `example_files` or `inbox_files`.

`ta-llm-input` is for student-facing retrieval. It must contain only approved
canonical lecture/source material after unified topic merging, plus exercises
after the generated bank has been verified. It should not expose raw
source/instructor splits as student-facing lecture files.

## Files In This Folder

- [PIPELINE_README.md](PIPELINE_README.md): operational overview for the
  general "dump my material" phase.
- [PHASE1_SPEC.md](PHASE1_SPEC.md): target behavior and artifacts.
- [HANDOFF_CONTRACTS.md](HANDOFF_CONTRACTS.md): exact contracts for
  `quiz-llm-bank` and `ta-llm-system`.
- [DECISION_GATES.md](DECISION_GATES.md): human checkpoints before generation
  or TA ingestion.
- [STARTUP_QUESTION_BANK.md](STARTUP_QUESTION_BANK.md): targeted question bank
  for resolving uncertainty after the first dump exploration.
- [templates/](templates): manifest and config templates. Template filenames
  are descriptive; emitted artifact names are defined in
  [HANDOFF_CONTRACTS.md](HANDOFF_CONTRACTS.md).
- [claude-prompts/](claude-prompts): prompts for Claude Opus 4.7 subagent
  audits.

## Public-Release Scope

Private historical course implementations are intentionally not shipped here.
This folder is the generalized design for a config-driven Phase 1 runner. Its
unified topic corpus behavior is the general default, not a course-specific
exception.
