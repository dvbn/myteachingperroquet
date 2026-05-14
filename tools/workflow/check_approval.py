#!/usr/bin/env python3
"""Check a workflow APPROVAL.json gate.

Exit 0 only when the approval file exists, lives at a canonical gate path,
matches the expected phase, and has status == "approved".
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


CANONICAL_SUFFIXES = {
    ("APPROVAL.setup.json",): "setup",
    ("phase1-output", "APPROVAL.json"): "phase1",
    ("phase2-output", "smoke", "APPROVAL.json"): "phase2-smoke",
    ("phase2-output", "full", "APPROVAL.json"): "phase2-full",
    ("phase3-output", "ingestion", "APPROVAL.json"): "phase3-ingestion",
    ("phase3-output", "deployment-preview", "APPROVAL.json"): "deployment-preview",
    ("phase3-output", "production", "APPROVAL.json"): "production",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check workflow approval gate")
    parser.add_argument("--approval", required=True, help="Path to APPROVAL.json")
    parser.add_argument("--phase", default=None, help="Expected phase name")
    parser.add_argument(
        "--allow-noncanonical",
        action="store_true",
        help="Skip canonical path checks. Intended only for tests or migrations.",
    )
    return parser.parse_args()


def expected_phase_from_path(path: Path) -> str | None:
    parts = path.parts
    for suffix, phase in CANONICAL_SUFFIXES.items():
        if len(parts) >= len(suffix) + 1 and parts[-len(suffix) :] == suffix:
            if phase == "setup" and not (path.parent / "workflow_config.json").exists():
                return None
            return phase
    return None


def main() -> int:
    args = parse_args()
    approval_path = Path(args.approval)
    if not approval_path.exists():
        print(f"BLOCKED: approval file not found: {approval_path}", file=sys.stderr)
        return 1

    expected_from_path = expected_phase_from_path(approval_path)
    if not args.allow_noncanonical and expected_from_path is None:
        print(
            f"BLOCKED: approval path is not a canonical workflow gate: {approval_path}",
            file=sys.stderr,
        )
        return 1

    if args.phase and expected_from_path and args.phase != expected_from_path:
        print(
            f"BLOCKED: requested phase {args.phase!r} does not match gate path "
            f"{expected_from_path!r}",
            file=sys.stderr,
        )
        return 1

    try:
        data = json.loads(approval_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"BLOCKED: invalid approval JSON: {exc}", file=sys.stderr)
        return 1

    phase = data.get("phase")
    if expected_from_path and phase != expected_from_path:
        print(
            f"BLOCKED: approval phase {phase!r} does not match gate path "
            f"{expected_from_path!r}",
            file=sys.stderr,
        )
        return 1

    if args.phase and phase != args.phase:
        print(
            f"BLOCKED: approval phase {phase!r} does not match expected {args.phase!r}",
            file=sys.stderr,
        )
        return 1

    status = data.get("status")
    if status != "approved":
        print(f"BLOCKED: approval status is {status!r}, not 'approved'", file=sys.stderr)
        return 1

    print(f"APPROVED: {approval_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
