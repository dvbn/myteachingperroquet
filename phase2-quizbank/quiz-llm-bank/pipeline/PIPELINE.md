# Pipeline Reference

Module-by-module reference for the exercise generation pipeline. The entry
points are the `Pipeline` helper class in `run.py` (orchestration) and the
seven validators under `validators/`.

For workflow / how-to-run, see `pipeline/README.md`. This document is the
detailed code map.

---

## Module map

```
run.py ─────────────────────── Pipeline class: aggregate, validate_batch,
                                relocate_exercises, apply_relocation,
                                audit/fix helpers, codex runner
prompt_renderer.py ─────────── Template engine, builds prompts from
                                course_config + scope_resolver
config_loader.py ───────────── Config loader, path helpers, DAG validation
scope_resolver.py ──────────── Scope logic (prereq closure, allowed/excluded
                                terms, scope-with-introduction-session
                                grouping)
postprocessor.py ───────────── related_exercises, topic normalization,
                                ID remapping (used by relocate_exercises)
schema_builder.py ──────────── Generates exercise JSON schema from config
catalog_generator.py ───────── EXERCISE_BANK_CATALOG.md generator
glossary_generator.py ──────── Bilingual glossary generator
findings_io.py ─────────────── Structured-finding collector for validators
sample_for_review.py ───────── Phase 6 stratified sampler (optional)
review_tool.py ─────────────── Phase 6 interactive CLI (optional)
validators/ ────────────────── 7 Phase 2 validators (see below)
tests/                        Pytest suite (95 tests across three files)
```

---

## `run.py` — `Pipeline` class

The orchestration helper. Phases 1 (generate), 3 (audit), 4 (fix) are
driven by an interactive agent that calls these methods; Phases 2
(validate) and 5 (review) are standalone scripts.

### Key methods

| Method | Purpose |
|--------|---------|
| `aggregate(session_id)` | Merge `batch_*_{LANG}.json` into `exercises_{LANG}.json`, sanitize, fill `related_exercises`, archive batches into `batches/`. **Warns on duplicate IDs but does not deduplicate** — the caller must avoid producing duplicates in the source batches |
| `validate_batch(exercises, session_id, language)` | Pre-aggregation gate: check topic scope and excluded-term references; returns violations |
| `relocate_exercises(id_map, session_ids=None)` | Apply `{old_id: new_id}` remapping across session JSON files: updates `id`, `twin_id`, `prerequisites`, `related_exercises`, then recomputes related |
| `apply_relocation(finding)` | Reclassify an exercise (and its twin) to the `target_session` named in an audit finding with `recommended_action == "reclassify"`. Allocates next free trailing number on collision |
| `audit_prompt(session_id)` | Render the self-audit prompt with all session exercises inlined |
| `save_findings(findings, session_id, source)` | Persist audit findings JSON to `validation/{source}_audit/` |
| `run_codex_audit(session_id)` | Spawn `codex exec` subprocess with the codex audit prompt; parse `findings_json` block from the markdown output and write to `validation/codex_audit/codex_audit_{session_id}_findings.json` |
| `get_flagged(session_id)` | Returns `{exercise_id: {"exercise": …, "findings": […]}}` for exercises with at least one critical/major finding |
| `fix_prompt(exercise, findings)` | Render the fix prompt for one exercise + its findings |
| `apply_fix(session_id, exercise_id, fixed_exercise)` | Replace the exercise in session JSON, refresh `related_exercises` |

### Reclassification (`apply_relocation`)

Driven by an audit finding shaped like:

```json
{
  "category": "forward_reference",
  "exercise_id": "S1_EN_MATH_005",
  "recommended_action": "reclassify",
  "target_session": "S8",
  "out_of_scope_concept": "instrumental variables"
}
```

Steps performed:

1. Locate the exercise + twin via `_find_exercise(id)` (scans all session files).
2. Compute new IDs in the target session via `_compute_paired_new_ids`,
   allocating the smallest trailing number that is free in BOTH the
   primary and twin language files (so the pair stays symmetric).
3. Physically move both entries between session JSON files
   (`_move_exercise_between_sessions`).
4. Call `relocate_exercises({old: new, twin_old: twin_new})` to update
   `id`, `twin_id`, `prerequisites`, and `related_exercises` across all
   session files; this also re-runs `compute_related`.
5. Returns `(new_id, new_twin_id)` for the caller to log.

The agent is responsible for re-running validators after a batch of
relocations (same as after a batch of fixes).

---

## `prompt_renderer.py` — Template engine

Renders prompt templates with config values and inlines slide content.

### Functions

| Function | Purpose |
|----------|---------|
| `render_generation_prompt()` | Phase 1: exercise generation (single-type batch variant) |
| `render_full_generation_prompt()` | Phase 1: exercise generation (full-batch variant; one batch per session per language, types proportional to `type_distribution`) |
| `render_twin_prompt()` | Phase 1: twin generation (single-type variant) |
| `render_full_twin_prompt()` | Phase 1: twin generation (full-batch variant) |
| `render_self_audit_prompt()` | Phase 3: combined Claude self-audit (math + pedagogy + scope) |
| `render_codex_audit_prompt()` | Phase 3: independent Codex audit |
| `render_fix_prompt()` | Phase 4: fix prompt for one flagged exercise |
| `build_batch_schema()` | Wrap the exercise schema in an array for batched generation |
| `write_prompt_to_temp()`, `write_schema_to_temp()` | Temp file helpers |

### Template syntax

```
{{variable_name}}          → simple substitution
{{#if var}}...{{/if}}      → conditional block (truthy check)
```

### Slide inlining

Generation prompts may inline slide files from `inbox/Slides/{session_id}/`
(or the session's configured `inbox_files`) when the agent runs without
file-reading tools, or pass file paths when it does. Total inlined size is
capped at `scaling.large_slide_max_chars` (default 200k).

---

## Audit prompts

The two audit prompts share a finding JSON schema. They cover four parts:

- **A — Math & factual correctness** (numerical answers, formulas, software
  syntax, derived quantities)
- **B — Pedagogy** (clarity, hints, difficulty, common mistakes, uniqueness)
- **C — Scope & coverage** (forward references, thin coverage)
- **D — Structural & bilingual** (twin parity, glossary, IDs, cross-refs;
  Codex only — `self_audit.md` covers parts A/B/C with a glossary check
  embedded in B)

### Forward references and thin coverage

Both prompts emit `forward_reference` (CRITICAL) and `thin_coverage`
(WARNING) findings with these fields beyond the standard schema:

- `recommended_action: "rewrite" | "reclassify" | "delete" | "keep"`
- `target_session: "<S_k>" | null`
- `out_of_scope_concept: "<term>" | null`
- `slide_evidence: "<file or slide ref>" | null`

`forward_reference` findings always carry `recommended_action: "reclassify"`
and a non-null `target_session`. The fix flow handles them via
`Pipeline.apply_relocation`.

---

## `scope_resolver.py` — Scope logic

Single source of truth for "what is session S allowed to reference?"

### Public API

| Function | Returns |
|----------|---------|
| `get_session_order(cfg)` | `{session_id: index}` — 0-based ordering |
| `get_prerequisite_closure(cfg, session_id)` | `set[str]` — transitive prerequisite session IDs |
| `get_allowed_terms(cfg, session_id, language)` | `list[str]` — own + prereq + foundational terms |
| `get_excluded_terms(cfg, session_id, language)` | `list[str]` — terms from later sessions |
| `get_grouped_scope_terms(cfg, session_id, language)` | `{"this_session": [(term, sid)], "prereq": [...], "forbidden": [...]}` — used by generation prompt and audit prompts to group terms by status |
| `parse_prerequisite_session_id(prereq_str, known_ids)` | Longest-match prerequisite session ID |
| `build_term_pattern(term)` | Word-boundary-aware regex (case-insensitive) |
| `extract_exercise_text(exercise)` | All scope-relevant text fields concatenated |

48 unit tests in `tests/test_scope_resolver.py` (including 7 for
`get_grouped_scope_terms` and 2 for case-sensitive acronym matching).
12 more in `tests/test_apply_relocation.py` cover the
audit-driven relocation flow. No dependency on
`config_loader.py` (avoids circular imports).

---

## `postprocessor.py` — related_exercises, normalization, remapping

| Function | Purpose |
|----------|---------|
| `compute_related(exercises)` | Per-language topic-overlap ranking; deterministic on ties |
| `normalize_topics(exercises, alias_map)` | Apply `topic_aliases`, dedupe |
| `flag_unmappable_topics(exercises, cfg)` | Warn on topics outside any session's configured topics |
| `remap_exercise_ids(exercises, id_map)` | Update `id`, `twin_id`, `prerequisites`, `related_exercises`. `ValueError` on many-to-one collisions |
| `sanitize_exercises(exercises)` | Coerce `data_table` objects to markdown strings; `common_mistakes: null` to `[]` |

All functions are pure (no I/O, no randomness).

---

## Phase 2 validators (`validators/`)

| Validator | What it checks |
|-----------|----------------|
| `validate_schema.py` | JSON schema conformance |
| `validate_structure.py` | Unique IDs, valid cross-references, sequential numbering |
| `validate_coverage.py` | Type/difficulty distribution matches config |
| `validate_bilingual.py` | Twin numerical parity, glossary compliance |
| `validate_math.py` | SymPy formula evaluation, t-critical values (scipy) |
| `validate_rag.py` | RAG-friendly text (balanced `$`, no malformed markup) |
| `validate_content_boundary.py` | Scope enforcement (excluded-term scan, novel-term detection, DAG self-test) |

Run individually or as a group:

```bash
PYTHONPATH=pipeline python3 pipeline/validators/validate_<name>.py
```

### `validate_content_boundary.py` self-test

Before exercise scanning, the validator checks:
1. Pattern self-match: every `scope_term` matches itself via
   `build_term_pattern`
2. Bilingual coverage: flags sessions where one language has >30% fewer
   `scope_terms` than another
3. DAG integrity: prerequisite graph is acyclic

The runtime scan flags excluded-term references and (heuristically) novel
terms — capitalized multi-word phrases or trigger-word patterns absent
from any session's `scope_terms`. The audit's `forward_reference` finding
is the LLM-judgment counterpart to this programmatic check.

---

## `findings_io.py` — Validator finding collector

`FindingCollector(source)` accumulates structured findings from Phase 2
validators and writes a JSON payload with timestamp + source. Audit
findings (Phase 3) come from LLM output and are parsed directly — they do
not flow through `FindingCollector`.

---

## `config_loader.py` — Config & paths

| Function | Returns |
|----------|---------|
| `load_config(path)` | Validated config dict |
| `get_output_dir(cfg)` | `output/<course_id>/` path |
| `get_session_path(cfg, session_id)` | Session output directory |
| `get_session_dirs(cfg)` | `{session_id: dir_name}` |
| `get_validation_dir(cfg)` | `output/<course_id>/validation/` |
| `get_scaling_config(cfg)` | Scaling section with defaults |
| `get_inbox_files(cfg, session_id)` | Resolved inbox file paths |
| `get_languages(cfg)` | Languages list (primary first) |

Validation in `_validate()`: required keys, language-keyed titles,
type/difficulty distributions, prerequisite DAG acyclicity, foundational
terms shape, alias guards.

---

## CLI summary

| Command | Purpose |
|---------|---------|
| `python3 pipeline/schema_builder.py [config]` | Generate `schema.json` |
| `python3 pipeline/run.py --info --sessions S1` | Print session status |
| `python3 pipeline/run.py --dry-run --sessions S1` | Render prompts only |
| `python3 pipeline/run.py --aggregate --sessions S1` | Merge batch files |
| `python3 pipeline/run.py --codex --sessions S1` | Run Codex audit subprocess |
| `python3 pipeline/postprocessor.py` | Refresh `related_exercises` |
| `python3 pipeline/catalog_generator.py` | Generate `EXERCISE_BANK_CATALOG.md` |
| `python3 pipeline/glossary_generator.py` | Generate bilingual glossary |
| `python3 pipeline/sample_for_review.py [config]` | Build review queue |
| `python3 pipeline/review_tool.py next` | Phase 6 interactive review |
| `PYTHONPATH=pipeline python3 pipeline/validators/validate_<name>.py` | Run one Phase 2 validator |
