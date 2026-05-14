# Phase 0: Interactive Course Setup Interview

Guide Claude Code through collecting all information needed to generate `course_config.json`.

## Pre-Interview: Scan Inbox

**Before asking any questions**, read the contents of `inbox/` to extract as much as possible automatically:

1. **Scan `inbox/Slides/`**: read file names and sample content from each session folder
2. **Scan assessment/practice material**: inspect `inbox/ExamExamples/` and any cases, assignments, rubrics, figures, graph prompts, datasets, games, or practice questions. Record sampled paths and observed question styles.
3. **Detect languages**: if materials exist in multiple languages (e.g., English and French versions of the same slides), the course is multilingual. Set languages automatically — no need to ask.
4. **Detect session structure**: infer session count, IDs, titles (in each language), and topics from folder names and slide content
5. **Detect software tool**: if slides reference Stata, R, Python, MATLAB etc., note it
6. **Detect domain**: infer from course titles and content
7. **Extract glossary**: scan all materials for domain-specific terminology. When materials are bilingual, identify term pairs where the same concept appears in both languages (e.g., "OLS" ↔ "MCO", "Standard error" ↔ "Erreur type"). Build the glossary from actual course content — do not ask the user to provide it manually.

Present your findings to the user for confirmation before proceeding. If
assessment/practice evidence is missing, do not propose exercise types from
domain labels alone; ask which material should drive the quizbank or mark
`assessment_style_basis` as `pending_assessment_style_audit`.

## Interview Flow

### Step 1: Course Identity
Ask the user (pre-fill from inbox scan where possible):
- What is the course name? (in each detected language)
- What institution is this for?
- What is the academic domain?
- What year/semester identifier should we use? (e.g., "winter_2026", "fall_2025")

Generate `course_id` as: `{domain}_{institution_slug}_{year}` (e.g., `econometrics_example_2026`)

### Step 2: Languages
**Auto-detect from inbox materials.** If materials are bilingual or multilingual, set languages automatically:
- The language with more content (or the one used for mathematical notation) is the primary language
- Other languages are secondary (twins are generated from primary)
- Only ask the user to confirm, not to specify from scratch

Set `"languages": [primary, secondary, ...]` in config.

### Step 3: Session Structure
**Auto-detect from inbox folder structure.** Present the inferred structure and ask the user to confirm/adjust:
- Session count, IDs, directory names
- Title in each language (extracted from slide headers)
- Main topics per session (extracted from slide content)
- Prerequisite topics from earlier sessions
- **Scope terms per session**: For each session, extract all *named* statistical tests, methods, estimators, and theorems (proper nouns, not general concepts) from the slides. Store as `scope_terms` with a list per language. These are used by the content boundary validator (Phase 2) and injected into generation prompts to prevent the LLM from drifting beyond what the slides actually teach. Example:
  ```json
  "scope_terms": {
    "en": ["Breusch-Pagan test", "White test", "GLS", "WLS"],
    "fr": ["test de Breusch-Pagan", "test de White", "MCG", "MCP"]
  }
  ```

  **Scope terms quality gates**:
  - **Self-match** (enforced by validator self-test): every scope_term must match its own regex pattern (`build_term_pattern(term).search(f" {term} ")` must succeed). If a term fails self-match, fix special characters.
  - **Bilingual coverage** (enforced by validator self-test): flag sessions where one language has >30% fewer scope_terms than another. Advisory — exact 1:1 is not required, but large gaps suggest missing translations.
  - **DAG integrity** (enforced by validator self-test): prerequisite graph must be acyclic.
  - **Minimum count** (manual guideline): each session should have >= 5 scope_terms per language. Fewer terms means the content boundary validator has little to check.
  - **Cross-session frequency** (manual guideline): if a term appears in 3+ sessions' scope_terms, it is a candidate for `foundational_terms` (a shared list that avoids duplication).

- **Foundational terms**: terms used across many sessions. Instead of duplicating them in each session's `scope_terms`, add them to the top-level `foundational_terms` with an `introduced_in` session. They become allowed from that session onward. Example:
  ```json
  "foundational_terms": {
    "en": [{"term": "confidence interval", "introduced_in": "S2"}],
    "fr": [{"term": "intervalle de confiance", "introduced_in": "S2"}]
  }
  ```

### Step 4: Assessment Style And Exercise Types

First show the evidence you inspected:

- sampled exams, corrections, question pools, assignments, rubrics, or practice files
- sampled cases, readings, figures, graphs, datasets, games, or software outputs
- observed question styles, e.g. open written questions, graphical analysis,
  yes/no, multiple-choice, case/source analysis, true/false, interpretation,
  calculations, or software output

Then ask the user:

- Should the quizbank mirror this observed assessment style, or should another
  source family drive the first run?
- I infer these exercise types and weights from the evidence: `<proposal>`.
  Should I use them for quiz mode?
- If a software tool, figures, graphs, cases, or calculations were actually
  present, should those appear as separate exercise types or be folded into
  broader open/case/interpretation types?
- Which inferred types should be visible in TA quiz mode, and which should be
  hidden or authoring-only?

Default type inference: map yes/no or true/false evidence to `YES_NO`,
multiple-choice evidence to `MCQ`, short open written prompts to `OPEN`, short
case applications to `CASE`, diagram work to `GRAPHICAL`, and numerical work to
`CALCULATION` only when calculations are actually central.

Set `assessment_style_basis` and `assessment_style_evidence` in the config.
If the evidence is incomplete, keep
`"assessment_style_basis": "pending_assessment_style_audit"` and do not run
generation.

### Step 5: Stage 2 Output Shape

Before generation, ask the user to confirm the exact output shape:

- Smoke run: how many exercises per session per language? Default: 10.
- Full run: how many exercises per session per language? Default: 30.
- Per-session overrides: should any session produce more or fewer exercises?
- Per-type quotas: should each session use the inferred distribution, or exact
  quotas such as 8 `OPEN`, 8 `CASE`, 6 `MCQ`, 4 `YES_NO`, and 4 `GRAPHICAL`
  out of 30?
- Smoke coverage: should the smoke run include at least one example of each
  enabled quiz-visible type when feasible? Default: yes.

The confirmed totals must be written into each session's `exercise_count`.
The confirmed type quotas must be written into each session's
`type_distribution`, and each distribution must sum to `exercise_count`.

### Step 6: Generation Batch Settings
Ask the user:
- How many exercises per generation batch? Default: 20
  - Each batch is one Claude call. Smaller batches = higher quality per exercise.
- How many generation loops per session? Default: 1
  - Total exercises per session = `batch_size × generation_loops`
  - Example: batch_size=20, generation_loops=3 → 60 exercises per session
- The type distribution from Step 5 will be scaled proportionally to
  `batch_size` for each loop.

Set `"batch_size"` and `"generation_loops"` in config.

### Step 7: Difficulty Distribution
Ask the user:
- What difficulty levels? Default: EASY, MED, HARD
- What target distribution? Default: EASY 30%, MED 45%, HARD 25%

### Step 8: ID Pattern
Generate an ID pattern dynamically from the configured sessions, languages, and types:
- Build the regex from actual session IDs, language codes, and exercise types
- Example: `^S\d+_(FR|EN)_(YES_NO|MCQ|OPEN|CASE|GRAPHICAL)_\d{3}$`
- Show the proposed pattern to the user for confirmation

### Step 9: Solution Constraints
Ask the user:
- Max solution length? Default: 300 words
- Number of hints? Default: 2-3
- Max hint length? Default: 150 words
- Which types require common_mistakes or rubric notes? Use the assessment
  evidence, e.g. graphical interpretation errors, open-question rubric gaps,
  case/source misuse, or calculation mistakes.
- Which solution fields are required? Default: `["text"]`. Add `key_formula`,
  `numerical_answer`, rubric notes, source citations, or figure-analysis
  criteria only when the inspected material calls for them.

### Step 9: Domain-Specific Templates (optional)
If relevant to the course domain:
- Does the course need a standard interpretation/answer template?
  - For regression courses: "When [X] increases by [unit], [Y] tends to be [higher/lower] by [value], on average, all else equal."
  - For other courses: define domain-appropriate templates or skip
- Templates should be provided in each configured language

### Step 10: Glossary
**Auto-generate from inbox scan.** The glossary is built by extracting bilingual term pairs from the course materials:
- Identify concepts that appear in both languages across slides
- Flag terms where a specific translation must be enforced (e.g., never "non biaisé", always "sans biais")
- Present the extracted glossary to the user for review — they can add, remove, or correct entries
- Do NOT ask the user to build the glossary from scratch

### Step 11: Validation Settings
- Does the course have numerical/mathematical exercises? If yes:
  - Relative tolerance: default 0.02 (2%)
  - Absolute tolerance: default 0.05
  - Statistical checks enabled? (t-tests, F-tests, critical values) — only for statistics courses
  - Set `math_validation.checks`: e.g., `["formula_eval"]` or `["formula_eval", "t_critical_values"]`
- Max fix iterations: default 3
- RAG ingestion enabled: default false

## Output

Generate `course_config.json` at the project root using `pipeline/config_loader.py` to validate.
Then run `pipeline/schema_builder.py` to generate `output/<course_id>/schema.json`.
Create session directories under `output/<course_id>/`.

## Key contract elements to memorize for the whole pipeline

- Never use background agents for this, do everything yourself except for Codex audits.
- Quality first, always
- Execute the whole pipeline without stopping
