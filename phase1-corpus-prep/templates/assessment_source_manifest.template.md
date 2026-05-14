# Assessment Source Manifest

| Source | Session | Language | Type | Has Correction | Destination | Notes |
|---|---|---|---|---:|---|---|
| `resources/...` | S1 | fr | past_exam | yes | moreexercices authoring only |  |

## Rules

- Past exams and corrections are used to calibrate question style and coverage.
- They must not be copied into `ta-llm-input/sources/lectures`.
- When assessment files live outside the auto-discovered
  `inbox/ExamExamples/<session.id>/` location, list paths explicitly in
  `session.example_files`.
