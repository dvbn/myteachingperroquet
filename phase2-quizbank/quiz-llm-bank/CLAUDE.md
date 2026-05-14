# Instructions — quiz-llm-bank

You (Claude / Codex / any LLM coding agent) are reading this because a
non-technical course instructor opened this repo to generate an exercise
bank. Your job is to walk them through it and drive the pipeline. They
will not write code; they shouldn't have to read JSON schemas or run
Python by hand.

## How the user is interacting with you

They have probably said something like:

- *"Set up a new course."*
- *"Help me make exercises for my course."*
- *"I have these PDFs of slides — can you turn them into exercises?"*

If their first message is fuzzy, do not ask twenty questions. Read the
top-level `README.md` to understand the workflow, then ask **one
focused question at a time** to learn what's needed.

## The user journey, mapped to actions

The README walks the user through four steps. Here's what each step
translates to on your end.

### Step 1 — They opened the repo

Nothing for you to do yet. Wait for their first task message.

### Step 2 — They say "set up a new course" (or similar)

This is **Phase 0 of the pipeline**: build a `course_config.json` with
the user's input.

1. Read `prompts/interview_guide.md` — it has the full Q&A flow and the
   structure of the config.
2. Walk the user through the questions, one at a time. Use the example
   in `examples/econometrics/course_config.json` as a reference shape.
3. Once you have enough, write the config to `./course_config.json` at
   the project root.
4. Run `python3 pipeline/schema_builder.py` to create `output/<course_id>/schema.json`.
5. Tell the user where their slides should go (`inbox/Slides/<session_id>/*.md`)
   and offer to convert PDFs / PPTX for them.

If their slides are in PDF or PPTX, you can convert them yourself (use
your file-reading tools and write markdown to `inbox/Slides/Sk/`). The
generator only reads markdown files.

### Step 3 — They say "go" / "generate" (or similar)

This is **Phases 1–4** of the pipeline. Drive it via the `Pipeline`
class in `pipeline/run.py`. The standard loop per session:

```python
from run import Pipeline
p = Pipeline()  # loads ./course_config.json

# --- Phase 1: Generation ---
for sid in [s["id"] for s in p.cfg["sessions"]]:
    # Primary language batches
    for loop in range(1, p.loops + 1):
        prompt = p.generation_prompt(sid, loop=loop)
        # Shell out to claude -p (see "Calling claude -p" below);
        # parse the JSON array from the fenced output.
        p.save_batch(exercises, sid, loop=loop, lang=p.primary.upper())

    # Twin language. The pipeline is bilingual — `p.secondary_langs[0]`
    # is the only twin language wired end to end. `target_lang` must be
    # the lowercase language code from `cfg["languages"]` (e.g. "fr"),
    # NOT the uppercase variant; the renderer keys glossary, course-name,
    # and interpretation-template lookups on it case-sensitively.
    target = p.secondary_langs[0]
    for loop in range(1, p.loops + 1):
        twin_prompt = p.twin_prompt(sid, loop=loop, target_lang=target)
        # Shell out to claude -p; parse twins JSON
        p.save_batch(twins, sid, loop=loop, lang=target.upper())

    # Aggregate batches into exercises_<LANG>.json files
    p.aggregate(sid)

# --- Phase 2: Validation (CLI) ---
# PYTHONPATH=pipeline python3 pipeline/validators/validate_<name>.py
# Run all seven; collect their stdout reports.

# --- Phase 3: Audit ---
for sid in [s["id"] for s in p.cfg["sessions"]]:
    findings = p.run_all_audits(sid)  # runs every configured verifier once
    # Legacy one-off wrapper if you explicitly need the old codex-only path:
    # p.run_codex_audit(sid)

# --- Phase 4: Fix ---
for sid in [s["id"] for s in p.cfg["sessions"]]:
    flagged = p.get_flagged(sid)  # {id: {exercise, findings}}
    for eid, info in flagged.items():
        for f in info["findings"]:
            action = f.get("recommended_action")
            if action == "reclassify":
                p.apply_relocation(f)         # moves to f["target_session"]
            elif action == "delete":
                # ASK THE USER before dropping. Do not silently delete.
                pass
            elif action == "keep":
                pass                          # auditor explicitly said keep
            else:
                # rewrite (default)
                fp = p.fix_prompt(info["exercise"], info["findings"])
                # Shell out to claude -p; parse the fixed exercise JSON
                p.apply_fix(sid, eid, fixed_exercise)

# --- Phase 5: Catalog (optional, but recommended for handoff) ---
# Run from CLI:
# python3 pipeline/catalog_generator.py
# Produces output/<course_id>/EXERCISE_BANK_CATALOG.md and
# output/<course_id>/glossary_<TWIN>_<PRIMARY>.{md,json}.

# --- Phase 6: Human review (optional) ---
# python3 pipeline/sample_for_review.py
# python3 pipeline/review_tool.py next
```

For end-to-end driver examples, see `scripts/run_experiment.py`,
`scripts/run_twin_generation.py`, and `scripts/run_codex_audits.py`.

## Provider configuration

The canonical place to configure LLM subprocesses is the top-level
`llm` field in `course_config.json`. `generation` configures Phase 1
generation/twin work; `verifiers` is a list of Phase 3 audit passes.
One verifier entry means one audit round in a fresh verifier context. Two
entries means two independent rounds. A verifier may use the same model as the
generator, but it must not reuse the generation conversation/context.

The Phase 3 audit runtime is wired through `pipeline/run.py` today.
The `generation` slot is part of the config schema, but the bundled
experiment scripts still shell out to Claude directly until they are
migrated to `pipeline/llm_providers.py`.

Default config (Claude generation + one separate Claude verifier):

```json
"llm": {
  "generation": {
    "provider": "claude",
    "model": "claude-opus-4-7",
    "api_key_env": null,
    "extra_args": []
  },
  "verifiers": [
    {
      "provider": "claude",
      "model": "claude-opus-4-7",
      "api_key_env": null,
      "extra_args": []
    }
  ]
}
```

Add a Codex external audit as a second verifier:

```json
"llm": {
  "generation": {
    "provider": "claude",
    "model": "claude-opus-4-7",
    "api_key_env": null,
    "extra_args": []
  },
  "verifiers": [
    {
      "provider": "claude",
      "model": "claude-opus-4-7",
      "api_key_env": null,
      "extra_args": []
    },
    {
      "provider": "codex",
      "model": "gpt-5.4",
      "api_key_env": null,
      "extra_args": []
    }
  ]
}
```

Switch to `openai`, `ollama`, or `vibe` the same way by changing the
`provider` and `model` fields, but note that those providers are stubbed
today: `pipeline/llm_providers.py` recognizes them and raises
`NotImplementedError` until you add `_call_openai()`, `_call_ollama()`,
or `_call_vibe()` in that file.

### Step 4 — They want to inspect or edit results

The output is plain JSON — read and summarize for them. For targeted
edits ("make all S2 hints more direct"), construct a fix
prompt with the user's instruction and call `Pipeline.apply_fix` per
affected exercise.

## Calling `claude -p` from inside this repo

`pipeline/llm_providers.py` is the canonical place to shell out to
Claude. If you need a direct call outside that dispatcher, prepend an
EXECUTION-MODE system prompt so the subprocess **executes** the rendered
template instead of treating it as a meta-message you sent to it:

```bash
claude -p \
    --model claude-opus-4-7 \
    --dangerously-skip-permissions \
    --append-system-prompt "EXECUTION MODE: The user's message is a structured prompt template. Execute it literally. Do not refuse or meta-comment." \
    < /tmp/prompt.txt
```

Without this override, the subprocess often refuses or asks
clarifying questions. With it, it produces the requested JSON or
markdown directly.

## Calling `codex exec` from inside this repo

`pipeline/llm_providers.py` is the canonical place to shell out to
Codex. The deprecated `Pipeline.run_codex_audit` wrapper ultimately uses
the same pattern:

```bash
codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check \
    -m <model> -C <project_root> -o <output_path> "<prompt>"
```

`--full-auto` does **not** work in hardened containers (no user
namespaces). Use the bypass flag. Clean `/tmp/codex-cache/*` before each
call to avoid disk-full errors.

## Autonomy rules

- **Run validators after any change** to exercise JSON files.
- **Don't ask permission** to run validators, copy files, or write under
  `output/`.
- **Do ask the user** before content-shaping decisions: which sessions to
  generate, which `software_tool` to use, whether to override an audit
  finding, whether to delete an exercise the auditor flagged.
- **One question at a time.** Non-technical users get overwhelmed by
  multi-question messages.
- **Never silently drop exercises.** Reclassify (via
  `Pipeline.apply_relocation`) when the audit recommends; rewrite when
  the audit recommends rewrite; only delete if the user explicitly
  confirms.
- **Never edit `inbox/` or `prompts/`** unless the user asks.

## Critical correctness constraints

- **Twin symmetry**: every exercise has a twin in each configured
  language; `twin_id` pairs must be reciprocal.
- **ID regex**: matches the configured `id_regex` (default
  `^S\d+_(EN|FR)_[A-Z]+_\d{3}$`).
- **Dollar signs in prose**: `\$` not `$` (LaTeX parser collision).
- **French standard error**: `\operatorname{ET}` not `ET`.
- **Scope**: an exercise in session S_k may only reference concepts in
  S1..S_k or in `foundational_terms` with `introduced_in <= S_k`. The
  generation prompt and the audit prompts both enforce this; you don't
  add extra checks beyond what they do.
- All seven validators must pass before the bank is considered
  release-ready.

## Audit finding categories

Standard categories: `correctness`, `math`, `pedagogy`, `format`, `twin`,
`glossary`.

Two scope-and-coverage categories specific to this repo:

- `forward_reference` (CRITICAL, blocking) — exercise's central topic is
  a concept introduced in a later session. The audit prompt always sets
  `recommended_action: "reclassify"` and a non-null `target_session`.
  Handle via `Pipeline.apply_relocation(finding)`.
- `thin_coverage` (WARNING) — exercise's primary topic appears in ~1
  slide of the session's material. May carry `reclassify`, `delete`, or
  `keep`. The auditor's call — respect it; if `keep`, the auditor
  explained the reasoning in the `evidence` field.

## When making non-trivial changes to the pipeline itself

If the user asks for changes to `pipeline/` or `prompts/` — not just
content edits but actual code or prompt-template changes — run an
independent Codex review of the changed files before committing:

```bash
rm -rf /tmp/codex-cache/* /tmp/codex-skills/* 2>/dev/null
codex exec -m gpt-5.4 -c model_reasoning_effort=xhigh \
    --dangerously-bypass-approvals-and-sandbox \
    --skip-git-repo-check -C . \
    "<audit prompt referencing the spec and the files you changed>"
```

If Codex flags issues, fix them. If there is a design conflict, surface it to
the user — don't silently choose a side.

## When in doubt

- **Lean on the user**: ask one targeted question.
- **Use the example**: `examples/econometrics/` shows a full bilingual
  bank you can pattern-match against.
- **Read the prompts**: `prompts/exercise_generation.md`, `self_audit.md`,
  `codex_audit.md`, `interview_guide.md`, `twin_generation.md` show the
  exact templates the pipeline feeds the LLM.
- **Read `pipeline/PIPELINE.md`**: module-level reference for every
  helper you'll touch.
