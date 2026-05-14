# Source Safety Checklist

Use this before Phase 1 emits downstream handoffs.

## Must Pass

- All raw source folders are inventoried or explicitly ignored.
- Duplicate files and generated derivatives are identified.
- Personal data, student data, grades, emails, secrets, and rosters are excluded.
- Spreadsheets and exports are quarantined unless explicitly approved as course
  datasets.
- Copyright-sensitive third-party sources are marked private, authoring-only, or excluded.
- Exams, corrections, answer keys, and rubrics are authoring-only.
- Transcripts and AI-generated summaries are quarantined unless targeted excerpts are approved.
- Source owners/instructors are recorded when known.
- Approved overlapping source families are routed into the unified topic
  corpus, not emitted as separate student-facing streams.
- Every source has a tier: `canonical`, `supplement`, `assessment_style`,
  `case_source`, `quarantine`, or `generated_scaffold`.

## Review Questions

- Are the canonical sources actually the instructor-approved course truth?
- Do approved variants have a clear precedence/conflict policy for the unified
  topic corpus?
- Are any active/reusable exams included by mistake?
- Are any corrections or answer keys exposed to student-facing retrieval?
- Are any raw dumps, spreadsheets, grades, or private exports present in online
  outputs?
- Are any noisy notes or transcripts being trusted too early?
- Are any third-party readings safe to process and deploy?

## Output Evidence

- `SOURCE_INVENTORY.md`
- `QUARANTINE_MANIFEST.md`
- `ASSESSMENT_SOURCE_MANIFEST.md`
- `SUPPLEMENT_SOURCE_MANIFEST.md`
- `SOURCE_NOTES.md`
