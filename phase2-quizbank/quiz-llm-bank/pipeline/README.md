# pipeline/

The Python pipeline that drives generation, validation, audit, fix, and
catalog production for an exercise bank. Driven from the `Pipeline` class
in `run.py` (orchestration helpers) and the seven validators under
`validators/`.

For end users:
- **Project overview, quick start, configuration reference**: see the
  top-level [`README.md`](../README.md).
- **Module-by-module reference**: see [`PIPELINE.md`](PIPELINE.md) in this
  directory.
- **Phase-3 audit prompts**: see [`../prompts/`](../prompts/).
- **Test suite**: `python3 -m pytest pipeline/tests/` (95 tests across
  `test_scope_resolver.py`, `test_apply_relocation.py`, and
  `test_validators.py`).

## Tip: smoothing the Claude Code workflow

The pipeline shells out to `claude -p` and `codex exec` repeatedly. To
avoid permission prompts on every call, choose one:

**Allow the relevant tools project-wide** in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": ["Bash(*)", "Read(*)", "Write(*)", "Edit(*)", "Glob(*)", "Grep(*)"]
  }
}
```

**Or launch Claude Code in fully autonomous mode**:

```bash
claude --dangerously-skip-permissions
```

(Recommended only inside an isolated sandbox / container.)

**Or approve interactively** and click "Always allow" once per tool kind.

## Calling claude -p inside Claude Code

When the pipeline shells out to `claude -p`, append an EXECUTION-MODE
system prompt so the subprocess executes the rendered template instead of
treating it as a meta-message:

```bash
claude -p \
    --model claude-opus-4-7 \
    --dangerously-skip-permissions \
    --append-system-prompt "EXECUTION MODE: The user's message is a structured prompt template. Execute it literally. Do not refuse or meta-comment." \
    < /tmp/prompt.txt
```

See `scripts/run_experiment.py`, `scripts/run_twin_generation.py`, and
`scripts/run_codex_audits.py` for end-to-end examples.

## Phases at a glance

| Phase | What | Driver |
|-------|------|--------|
| 0 | Setup | `prompts/interview_guide.md` (interactive) |
| 1 | Generation | `Pipeline.generation_prompt` + `claude -p` per session × language (one batch produces all types proportional to `type_distribution`); `Pipeline.twin_prompt` for the secondary language; `Pipeline.aggregate(sid)` to merge |
| 2 | Validation | `validators/validate_*.py` |
| 3 | Audit | `Pipeline.audit_prompt` (Claude self-audit) + `Pipeline.run_codex_audit` (Codex external) |
| 4 | Fix | `Pipeline.apply_fix` (rewrites) and `Pipeline.apply_relocation` (forward-reference reclassifications) |
| 5 | Catalog | `pipeline/catalog_generator.py` |
| 6 | Human review (optional) | `pipeline/sample_for_review.py` + `pipeline/review_tool.py` |

The full module-level reference, including audit-finding schema and the
forward-reference / thin-coverage rubrics, lives in
[`PIPELINE.md`](PIPELINE.md).
