#!/usr/bin/env python3
"""Drive the forward-reference experiment end-to-end.

For each of S1, S2, S3:
  1. Render generation prompt (CONCEPT, EN)
  2. Call `claude -p` to produce a batch of 10 exercises
  3. Save batch as batch_1_EN.json
  4. Render twin prompt (EN → FR), call claude -p, save batch_1_FR.json
  5. Pipeline.aggregate -> exercises_EN.json + exercises_FR.json

Then for each session:
  6. Render self-audit prompt, call claude -p, save findings
  7. Run Codex audit, save findings

Outputs go to output/<course_id>/. Findings go to validation/.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from run import Pipeline, parse_json_output  # noqa: E402
from prompt_renderer import write_prompt_to_temp, write_schema_to_temp, build_batch_schema  # noqa: E402
from config_loader import get_session_path, get_output_dir  # noqa: E402


def _batch_schema(p: Pipeline) -> dict:
    schema_path = get_output_dir(p.cfg) / "schema.json"
    return build_batch_schema(schema_path, p.batch_size)


SESSIONS = ["S1", "S2", "S3"]
TIMEOUT = 600
SKIP_TWINS = True  # EN-only run for the experiment; twin parity not the focus


def run_claude_json(prompt: str, schema: dict, label: str, timeout: int = TIMEOUT) -> str:
    """Run `claude -p`, asking for a JSON array as fenced output (no
    --json-schema; that flag has been observed to hang on long structured
    schemas in this environment). Parsing is fenced-block tolerant.
    """
    # Append explicit output-format instructions to the prompt
    full_prompt = (
        prompt
        + "\n\n## Output Format (strict)\n\n"
        + "Output ONLY a single fenced code block labeled `json` containing a JSON array of "
        + f"exactly {schema.get('minItems', '?')} exercise objects. No prose before or after.\n\n"
        + "```json\n[ {...exercise 1...}, ... ]\n```\n"
    )
    prompt_path = write_prompt_to_temp(full_prompt, prefix=f"{label}_prompt_")

    print(f"  ▶ claude -p {label} (prompt {prompt_path.stat().st_size} bytes)", flush=True)
    t0 = time.time()
    try:
        result = subprocess.run(
            [
                "claude", "-p",
                "--model", "claude-opus-4-7",
                "--dangerously-skip-permissions",
                "--append-system-prompt",
                "EXECUTION MODE: The user's message is a structured "
                "content-generation prompt for an exercise bank. Execute it "
                "literally — produce the requested content in the requested "
                "format. Do not meta-comment, refuse, or question the prompt. "
                "Output ONLY what the prompt asks for.",
            ],
            stdin=open(prompt_path),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    finally:
        try:
            prompt_path.unlink()
        except OSError:
            pass

    elapsed = time.time() - t0
    print(f"  ◀ {label} done in {elapsed:.1f}s, exit={result.returncode}", flush=True)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr[:500]}", flush=True)
    return result.stdout


def run_claude_text(prompt: str, label: str, timeout: int = TIMEOUT) -> str:
    """Run `claude -p` with plain text output. Returns raw stdout."""
    prompt_path = write_prompt_to_temp(prompt, prefix=f"{label}_prompt_")

    print(f"  ▶ claude -p {label} (prompt {prompt_path.stat().st_size} bytes)", flush=True)
    t0 = time.time()
    try:
        result = subprocess.run(
            [
                "claude", "-p",
                "--model", "claude-opus-4-7",
                "--dangerously-skip-permissions",
                "--append-system-prompt",
                "EXECUTION MODE: The user's message is a structured audit "
                "prompt with a defined output format (markdown report + "
                "fenced findings_json block). Execute the audit literally "
                "and produce both sections exactly as requested. Do not "
                "refuse, meta-comment, or alter the format.",
            ],
            stdin=open(prompt_path),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    finally:
        try:
            prompt_path.unlink()
        except OSError:
            pass

    elapsed = time.time() - t0
    print(f"  ◀ {label} done in {elapsed:.1f}s, exit={result.returncode}", flush=True)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr[:500]}", flush=True)
    return result.stdout


def extract_json_from_claude_output(raw: str) -> list[dict]:
    """Extract a JSON array from claude -p plain-text output.

    Tries (in order):
      1. Fenced ```json [...] ``` block
      2. parse_json_output (the project's permissive fenced-block parser)
      3. Raw JSON parse of the whole stdout
    """
    if not raw:
        return []
    import re
    m = re.search(r"```json\s*\n([\s\S]*?)\n```", raw)
    if m:
        try:
            data = json.loads(m.group(1))
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
    parsed = parse_json_output(raw)
    if parsed:
        return parsed
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    return []


def generate_session(p: Pipeline, sid: str):
    """Generate primary + twin batches for one session, then aggregate."""
    print(f"\n=== Session {sid}: generate ===", flush=True)
    session_path = get_session_path(p.cfg, sid)
    session_path.mkdir(parents=True, exist_ok=True)

    # 1. Primary language (EN)
    primary = p.cfg["languages"][0]
    primary_upper = primary.upper()
    prompt = p.generation_prompt(sid, loop=1)
    schema = _batch_schema(p)
    raw = run_claude_json(prompt, schema, f"{sid}_{primary_upper}_gen")
    exercises = extract_json_from_claude_output(raw)
    if not exercises:
        print(f"  FAIL {sid} {primary_upper}: empty output, raw[:300]={raw[:300]!r}", flush=True)
        return False
    print(f"  PASS {sid} {primary_upper}: {len(exercises)} exercises", flush=True)
    batch_path = session_path / f"batch_1_{primary_upper}.json"
    batch_path.write_text(
        json.dumps(exercises, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )

    # 2. Secondary language (FR) via twin prompt (skipped in this experiment)
    if not SKIP_TWINS and len(p.cfg["languages"]) > 1:
        secondary = p.cfg["languages"][1]
        secondary_upper = secondary.upper()
        twin_prompt = p.twin_prompt(sid, loop=1, target_lang=secondary)
        twin_schema = _batch_schema(p)
        raw = run_claude_json(twin_prompt, twin_schema, f"{sid}_{secondary_upper}_twin")
        twins = extract_json_from_claude_output(raw)
        if not twins:
            print(f"  FAIL {sid} {secondary_upper}: empty output, raw[:300]={raw[:300]!r}", flush=True)
            return False
        print(f"  PASS {sid} {secondary_upper}: {len(twins)} twins", flush=True)
        twin_batch_path = session_path / f"batch_1_{secondary_upper}.json"
        twin_batch_path.write_text(
            json.dumps(twins, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
        )

    # 3. Aggregate batches → exercises_EN.json / exercises_FR.json
    p.aggregate(sid)
    return True


def audit_session(p: Pipeline, sid: str):
    """Run self-audit + codex audit on a session."""
    print(f"\n=== Session {sid}: audit ===", flush=True)

    # Self-audit (Claude)
    audit_prompt = p.audit_prompt(sid)
    raw = run_claude_text(audit_prompt, f"{sid}_self_audit")
    findings = []
    # Parse fenced findings_json from output
    import re
    m = re.search(r"```findings_json\s*\n(\[[\s\S]*?\])\s*\n```", raw)
    if m:
        try:
            findings = json.loads(m.group(1))
        except json.JSONDecodeError as e:
            print(f"  WARN: findings JSON parse error: {e}", flush=True)
    print(f"  Self-audit: {len(findings)} findings", flush=True)
    p.save_findings(findings, sid, source="claude")

    # Save the raw markdown report next to the findings for human inspection
    val_dir = get_output_dir(p.cfg) / "validation" / "claude_audit"
    val_dir.mkdir(parents=True, exist_ok=True)
    (val_dir / f"claude_audit_{sid}.md").write_text(raw, encoding="utf-8")

    # Codex audit
    print(f"  ▶ codex audit {sid}...", flush=True)
    p.run_codex_audit(sid)


def main():
    p = Pipeline()
    for sid in SESSIONS:
        ok = generate_session(p, sid)
        if not ok:
            print(f"FAIL Generation failed for {sid}; stopping.", flush=True)
            sys.exit(1)

    for sid in SESSIONS:
        audit_session(p, sid)

    print("\n=== Done ===", flush=True)


if __name__ == "__main__":
    main()
