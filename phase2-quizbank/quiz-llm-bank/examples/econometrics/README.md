# Econometrics example

A **sample run** showing what the pipeline produces, including audit
findings — not a polished, hand-curated bank. Browse it to see the
format and the kinds of issues the reviewers catch.

## What's here

- `course_config.json` — the configuration for an introductory
  econometrics course at *Example University* (a placeholder you'd
  replace with your own course details).
- `output/` — a single end-to-end run under this configuration:
  - 3 sessions (S1: simple linear regression, S2: SLR properties, S3: multiple regression)
  - 10 exercises per session in English
  - 10 bilingual French twin exercises per session
  - 60 exercises total
  - Validation reports + Claude self-audit + Codex external audit
    findings alongside

The other 6 sessions (S4–S9, covering inference, functional forms,
heteroskedasticity, autocorrelation, instrumental variables, and panel
data) are **defined in the config but ship with no exercises**. Why?
Because the AI auditor needs to know about those later sessions to
detect when a generated exercise accidentally references a "later"
concept — but the example is intentionally trimmed to the first three
sessions to keep the bundle small.

## What state is the bank in?

This is a **first-pass run**. The bank passes all seven Phase-2
validators. The Phase-3 audits (Claude self-audit + independent Codex
external audit) surfaced 23 real findings across the three sessions —
left **intentionally unfixed** so you can see what each rubric catches.

Highlights (full reports under `output/validation/`):

- **`forward_reference` (S1)** — both audits flag the dataset-types
  classification exercise (`S1_EN_CONCEPT_001`, `S1_FR_CONCEPT_001`)
  as drifting toward panel data, which is properly taught in S9.
  Auditor recommendation: `reclassify` to S9 — this is exactly the
  scenario `Pipeline.apply_relocation` is designed for. Whether to
  follow the recommendation is a judgment call (the exercise is at
  least defensible as an introduction in S1); the audit gives you the
  data to decide.
- **`pedagogy` hint leakage (S2)** — Codex flags 8 CRITICAL findings
  on S2 (4 EN + 4 FR twins) where Hint 2 or 3 effectively reveals the
  answer. These would be fixed via `Pipeline.apply_fix` with an
  instruction to make hints more direct.
- **`correctness` on under-identified problems (S3)** —
  `S3_EN_CONCEPT_009` / `S3_FR_CONCEPT_009`: part (b) asks for a sign
  conclusion that the data given does not actually identify. Both
  audits agree; needs a rewrite.
- **`glossary` leak (S3 FR)** — Codex catches the French solution to
  `S3_FR_CONCEPT_008` expanding **BLUE** with English words ("Best
  Linear Unbiased Estimator") instead of the French expansion. This
  is the kind of cross-language glossary slip the codex audit missed
  before the glossary table was embedded in its prompt.

Why ship a bank with known issues? Because **the audit is the value**.
A polished hand-curated example would hide what the system actually
does for you. In a real run, your AI assistant would feed each finding
back to the appropriate fix method (`apply_fix`, `apply_relocation`)
before shipping to students.

## What you can do with this example

- **Look at the exercise files** (`output/.../exercises_EN.json`,
  `exercises_FR.json`) to see the format. They're JSON but readable
  as-is.
- **Look at the audit findings** (`output/validation/`) to see what the
  reviewers flagged. The hint-leak findings on S2 are particularly worth
  a read — they show how careful the audit can be.
- **Compare an EN exercise to its FR twin** (same trailing number) to
  see how bilingual parity works.

## Reusing this configuration for your own course

Tell the assistant: *"Start a new course based on the econometrics
example, but for [my topic]."* It will adapt the structure (session
count, type distribution, language pair, glossary) to your needs.

If you teach econometrics yourself and want to use this example as a
starting point: copy `course_config.json` to the project root, replace
the institution / instructor placeholders, drop your own slides into
`inbox/Slides/S1/` … `S9/`, and ask the assistant to generate.

## A note about Stata

The example config sets `software_tool: "Stata"` because the original
course uses Stata. The bundled S1/S2/S3 exercises don't include any
software-typed exercises — but if you regenerate with this config and
include `SOFTWARE` in the type distribution, the AI will write Stata
code in those exercises. To target R, Python, MATLAB, or any other
tool, just change the `software_tool` value before generating.
