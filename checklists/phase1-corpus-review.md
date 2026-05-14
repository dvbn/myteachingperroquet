# Phase 1 Corpus Review Checklist

Use this at the Phase 1 approval gate.

## Source And Routing

- Session map matches the pedagogical order.
- Topics are routed by content, not misleading filenames.
- Multiple instructor/source variants are merged into one unified topic corpus
  when approved.
- Raw variants are preserved in manifests, not duplicated in TA lectures.
- Forward-reference boundaries are explicit.
- Scope terms and foundational terms are plausible for each session.

## Markdown Quality

- Converted lectures are readable Markdown.
- Unified corpus files use one coherent course voice and are organized by
  topic, not by instructor, deck, raw filename, or source family.
- Headings are meaningful for TA chunking.
- Math and tables are preserved well enough for retrieval.
- Figure-only content is flagged for human review or alt-text follow-up.
- Filenames avoid preflight-triggering labels like `solution`, `correction`,
  `exercise`, `problem`, and `case` in lecture trees.

## Handoff Safety

- `moreexercices-input/inbox/Slides/` contains the unified topic corpus.
- Authoring-only material is tagged and outside default TA retrieval.
- `ta-llm-input/sources/lectures/` contains only the approved unified topic
  corpus and explicitly approved supplements.
- `ta-llm-input/sources/exercises/` is empty unless verified exercises already exist.
- `DOWNSTREAM_CHANGE_REQUESTS.md` exists, even if empty.

## Assessment Style Evidence

- `ASSESSMENT_STYLE_AUDIT.md` cites actual sampled paths, not just directory
  names.
- The audit includes exams, corrections, question pools, assignments, rubrics,
  cases, figures/graphs, games, datasets, or practice material when present.
- The proposed Phase 2 smoke profile mirrors observed assessment style.
- Exercise type labels match observed formats directly, such as `YES_NO`,
  `MCQ`, `OPEN`, `CASE`, `GRAPHICAL`, or `CALCULATION`.
- Math-heavy defaults are not used unless calculations are actually central in
  the sampled evidence.
- Graphical, open-question, case/source-analysis, or rubric-based assessment
  styles are flagged for Phase 2 prompt/schema/validator needs.

## Output Evidence

- `human-verification/README.md`
- `human-verification/ALL_CORPUS.md`
- `ASSESSMENT_STYLE_AUDIT.md`
- `LECTURE_SOURCE_TAGS.md`
- `SESSION_MAP.md`
- `PREFLIGHT_REPORT.md`
- Phase 1 gate: `courses/<course_id>/phase1-output/APPROVAL.json`
