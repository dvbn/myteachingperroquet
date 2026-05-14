# TA Ingestion Checklist

Use this before deployment planning.

## Source Tree

- `sources/lectures/` contains only approved canonical or explicitly approved
  supplement content.
- Lecture content is the unified topic corpus, not parallel raw streams by
  instructor, source family, deck, or filename.
- The approved setup-time ingestion scope is followed.
- Lecture files are organized under `S1/`, `S2/`, ...
- No exams, corrections, answer keys, rubrics, authoring guides, or quarantined
  content are present in lecture retrieval.
- No raw dumps, spreadsheets, grade files, or private exports are present.
- `sources/SOURCES.md` summarizes provenance without leaking private material.
- `data/course_config.json` matches the approved course and feature settings.

## Exercise Tree

- Quiz mode is disabled if no verified exercise bank exists.
- Exercise JSON came from approved Phase 2 output.
- Quiz-mode UX matches setup decisions: session selector, question-type
  selector, All option, and random/fixed ordering.
- Quiz-visible exercise types are short-form and compatible with the
  `course_ta` runtime; hidden long-form types are configured in
  `hidden_question_types`.
- `npm run transform` creates non-empty `data/exercise_index.json` when quiz
  mode is enabled.
- Software exercise fields are compatible with the current TA transformer.

## Build Commands

Run and record results:

- `npm run preflight`
- `npm run chunk`
- `npm run transform`
- `npm run rebuild`
- `npm run vectors`

## Output Evidence

- `data/lecture_chunks.json`
- `data/exercise_index.json`
- `data/tutor_corpus.json`
- `data/tutor_vectors.json`
- ingestion report
- ingestion gate: `courses/<course_id>/phase3-output/ingestion/APPROVAL.json`
