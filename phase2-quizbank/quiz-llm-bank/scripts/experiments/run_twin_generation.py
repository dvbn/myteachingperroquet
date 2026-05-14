#!/usr/bin/env python3
"""Generate FR twins for the existing EN exercises in S1, S2, S3.
Uses claude -p with --append-system-prompt to bypass meta-questioning."""

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "scripts" / "experiments"))

from run import Pipeline  # noqa: E402
from config_loader import get_session_path  # noqa: E402
from prompt_renderer import write_prompt_to_temp  # noqa: E402
from run_experiment import extract_json_from_claude_output  # noqa: E402


def run_claude(prompt: str, label: str, timeout: int = 600) -> str:
    prompt_path = write_prompt_to_temp(prompt, prefix=f"{label}_prompt_")
    print(f"  ▶ {label} (prompt {prompt_path.stat().st_size} bytes)", flush=True)
    t0 = time.time()
    try:
        result = subprocess.run(
            [
                "claude", "-p",
                "--model", "claude-opus-4-7",
                "--dangerously-skip-permissions",
                "--append-system-prompt",
                "EXECUTION MODE: The user's message is a structured "
                "translation prompt for an exercise bank twin generator. "
                "Translate the source exercises into the target language as "
                "instructed. Do not refuse, meta-comment, or alter the "
                "format. Output ONLY the requested JSON.",
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


def main():
    p = Pipeline()
    for sid in ["S1", "S2", "S3"]:
        print(f"\n=== {sid} twin generation (FR) ===", flush=True)

        # Append output-format instructions to the rendered twin prompt
        twin = p.twin_prompt(sid, loop=1, target_lang="fr")
        twin += (
            "\n\n## Output Format (strict)\n\n"
            "Output ONLY a single fenced ```json block containing a JSON "
            "array of exactly 10 twin exercise objects in French. No prose "
            "before or after the block.\n\n"
            "```json\n[ {...exercise 1...}, ... ]\n```\n"
        )

        raw = run_claude(twin, f"{sid}_FR_twin")
        twins = extract_json_from_claude_output(raw)
        if not twins:
            print(f"  FAIL {sid} FR: empty output, raw[:300]={raw[:300]!r}", flush=True)
            continue
        print(f"  PASS {sid} FR: {len(twins)} twins", flush=True)
        session_path = get_session_path(p.cfg, sid)
        batch_path = session_path / "batch_1_FR.json"
        batch_path.write_text(
            json.dumps(twins, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
        )
        # Aggregate to refresh exercises_FR.json
        p.aggregate(sid)


if __name__ == "__main__":
    main()
