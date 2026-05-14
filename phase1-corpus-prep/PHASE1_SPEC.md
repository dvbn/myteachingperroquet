# Phase 1 Specification

## Goal

Convert a raw teaching-material dump into structured, reviewable, downstream
ready artifacts without inventing course content.

Phase 1 is extraction, routing, tagging, normalization, and verification. It may
create metadata, manifests, source excerpts, and scaffolding, but it must label
all generated scaffolding separately from source truth.

## Inputs

Expected raw inputs are course-specific and may include:

- lecture slides: PDF, PPTX, LaTeX, Markdown, HTML, images;
- syllabus/course outline;
- lecture notes;
- transcripts;
- past exams, corrections, question pools;
- readings, case studies, datasets, classroom activities;
- interactive tools or generated figures.

No source should be assumed canonical until it is classified.

## Source Tiers

| Tier | Meaning | Default Destination |
|---|---|---|
| `canonical` | instructor-approved course content | unified topic corpus files in `ta-llm-input/sources/lectures` and `moreexercices-input/inbox/Slides` |
| `supplement` | relevant but secondary content | moreexercices authoring; TA only after approval |
| `assessment_style` | past questions, exams, corrections | moreexercices authoring only |
| `case_source` | readings/cases for realistic prompts | moreexercices authoring; TA only if approved as reading |
| `quarantine` | noisy, AI-enriched, transcript-like, duplicate, spreadsheet, sensitive, uncertain | human verification only unless explicitly admitted |
| `generated_scaffold` | generated question seeds, guides, prompts | moreexercices authoring only, never source truth |

## Core Stages

1. Inventory raw files.
2. Classify each source by type, risk, language, owner, and intended use.
3. Normalize course sessions/topics from the syllabus or instructor-provided
   map.
4. Route source slices by topic, not by filename/session number when those
   differ.
5. Convert sources into clean Markdown with visible provenance tags.
6. Merge approved lecture/source slices into one topic-organized lecture file
   per session for downstream lecture consumers.
7. Extract assessment examples and source examples for authoring.
8. Emit `moreexercices` config and inbox.
9. Emit `ta-llm-system` lecture sources and config.
10. Emit human-verification Markdown.
11. Run automated preflight checks and independent Claude/Codex audits.
12. Record required downstream changes without implementing them mid-phase.
13. Stop for human approval before exercise generation, TA ingestion, or
    downstream repo edits.

## Unified Topic Corpus Default

The default downstream lecture artifact is not a raw source file, not a
parallel instructor/source split, and not a bundle of disconnected excerpts. It
is one unified, source-grounded course corpus for each approved session/topic
bucket. This unified corpus is the content boundary that feeds both quiz
generation and TA retrieval.

Required behavior:

- merge only approved source slices;
- merge by normalized topic, not by instructor, filename, deck, or term;
- use one coherent pedagogical voice for the course;
- deduplicate overlapping explanations and preserve the clearest course-level
  statement;
- surface unresolved contradictions in the review artifacts instead of silently
  choosing;
- allow source-grounded synthesis and light rewriting for coherence, but never
  introduce claims not supported by the approved sources;
- use normalized topic headings;
- avoid source/instructor labels in student-facing headings and filenames;
- keep raw source provenance in manifests and human-verification artifacts.

The agent must not ask whether raw instructor/source variants should be
emitted as the default downstream corpus. That is not the default. The only
startup decision is source precedence and whether any source is unsafe,
outdated, or authoring-only.

This default applies to both:

- `moreexercices-input/inbox/Slides/<session.dir>/lecture_<session.id>_topics_merged.md`
- `ta-llm-input/sources/lectures/<session.id>/lecture_<session.id>_topics_merged.md`

## Required Provenance Tags

Each raw converted source or human-verification slice should start with visible
metadata:

```md
> **Tags corpus:** `session:S3`, `source_type:lecture_slides`, `source_role:raw_topic_source`, `source_quality:canonical`
> **Source:** `resources/...`
> **Generated file:** `phase1-output/...`
> **Routing:** topic or session route
> **Caveat:** optional quality warning
```

Required tag fields:

- `session`
- `source_type`
- `source_role`
- `source_quality`
- `source_instructor` or `source_owner` when known
- `authoring_only:true` when the material must not enter TA retrieval

Each merged downstream lecture should have a compact header:

```md
> **Tags corpus:** `session:S3`, `source_role:merged_topic_lecture`, `source_type:merged_lecture_slides`
> **Séance cible:** S3 — title
> **Provenance détaillée:** see `LECTURE_SOURCE_TAGS.md`
```

Allowed route destinations:

- `moreexercices`: emit to the authoring package only;
- `ta_llm`: include in the approved topic merge for the student-facing TA
  source package;
- both destinations may be used for canonical material.

## Output Guarantees

Phase 1 must guarantee:

- all downstream files are reproducible from raw sources plus config once the
  reusable runner exists; interim course-specific scripts must document any
  hardcoded routing;
- all generated/scaffolded content is tagged;
- downstream lecture files are unified by topic by default, not split by raw
  instructor/source variant;
- all exam/correction material is excluded from TA lecture retrieval;
- all raw dumps, spreadsheets, grade sheets, and private exports are excluded
  from deployable TA outputs unless a specific file is approved as a course
  dataset;
- all quarantined material has an explicit reason;
- `moreexercices` can read the emitted `course_config.json`;
- `ta-llm-system` preflight can scan emitted lecture/exercise sources;
- TA lecture filenames avoid preflight-triggering labels such as `solution`,
  `correction`, `exercise`, `problem`, and `case` unless intentionally emitted
  outside the lecture tree;
- humans can review the same content in Markdown before generation.
- downstream changes needed for `quiz-llm-bank` or `ta-llm-system` are captured
  in `DOWNSTREAM_CHANGE_REQUESTS.md` for the workflow-alignment checkpoint.
