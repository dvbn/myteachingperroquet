# sources/

This is where your content lives — the material the assistant will draw from
when answering questions.

The folder ships with a small public-domain example (the first five chapters
of *Three Men in a Boat* by Jerome K. Jerome — see `SOURCES.md`). Run the
pipeline against it as-is to verify the deploy, then replace it with your own
material.

For private course deployments, replace these files only in a private deploy
clone or through the gitignored `courses/<course_id>/phase3-output/` handoff.
Do not commit private lecture notes, raw dumps, student data, exams, answer
keys, or generated exercise banks to the public repository.

## Layout

```
sources/
  lectures/
    S1/
      chapter_01.md
    S2/
      chapter_02.md
    ...
  exercises/         # optional — only needed if you want a quiz mode
    S1/
      exercises_EN.json
      exercises_FR.json
    ...
```

The `S1`, `S2`, ... directory naming is required by the pipeline (the prefix
must be `S` followed by a number). They are simply ordered "sections" of your
content — chapters of a book, lectures of a course, parts of a paper, sections
of a manual. Treat them as ordered groupings, not as anything course-specific.

## Lectures (required)

Plain markdown files, one per section topic. The pipeline splits each file
into retrievable chunks automatically — you don't need to chunk by hand.

Subheadings (`##`, `###`), code blocks, tables, and inline math (`$...$` or
`$$...$$` with KaTeX) all work. Avoid HTML.

## Exercises (optional)

If you want quiz mode (multi-step practice questions with hints and
solutions), add JSON files under `exercises/`. The schema is defined in
`schema/exercise_schema.json` and a minimal bilingual exercise pair looks like:

```json
[
  {
    "id": "S1_EN_CONCEPT_001",
    "twin_id": "S1_FR_CONCEPT_001",
    "session": "S1",
    "session_title_en": "Introduction",
    "session_title_fr": "Introduction",
    "language": "en",
    "question_type": "CONCEPT",
    "difficulty": "EASY",
    "topics": ["estimation"],
    "prerequisites": [],
    "lecture_ref": "S1.2",
    "question_text": "What does OLS stand for?",
    "data_table": null,
    "solution": {
      "text": "OLS stands for Ordinary Least Squares. It minimizes the sum of squared residuals.",
      "key_formula": null,
      "numerical_answer": null,
      "common_mistakes": []
    },
    "hints": [
      "Think about what is being minimized.",
      "The name describes both the method and its objective."
    ],
    "related_exercises": [],
    "stata_code": null
  }
]
```

The bilingual twin is the same exercise in French with `"language": "fr"` and
the `twin_id` pointing back. Both must exist together if you want bilingual
quiz support.

**Constraints:**
- `difficulty` is `EASY`, `MED`, or `HARD` (uppercase).
- `hints` requires 2–3 items.
- Every exercise needs a `twin_id` if you ship more than one language.

In the full MyTeachingPerroquet workflow, verified exercise banks are produced
by Phase 2 and copied into `sources/exercises/` only after human approval.

## Running the pipeline

```bash
npm run preflight    # validate sources/ structure
npm run chunk        # split lectures into chunks → data/lecture_chunks.json
npm run transform    # process exercises → data/exercise_index.json (skipped if no exercises)
npm run rebuild      # merge into corpus → data/tutor_corpus.json
npm run vectors      # generate embeddings → data/tutor_vectors.json (calls OpenAI)
```
