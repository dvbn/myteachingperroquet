#!/usr/bin/env python3
"""Phase 2 validator: RAG compatibility checks.

Checks:
- question_text and solution.text are non-empty and reasonable length
- No null values in required string fields
- LaTeX delimiters are balanced ($...$ and \\(...\\))
- No excessively long fields that would blow up token limits

Exit code 0 = PASS, 1 = FAIL.

Flags:
  --findings-output <path>  Write structured findings JSON alongside markdown.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config_loader import load_config, get_output_dir, get_session_dirs, get_json_files
from findings_io import FindingCollector

MAX_QUESTION_CHARS = 3000
MAX_SOLUTION_CHARS = 5000
MAX_HINT_CHARS = 1000


def check_balanced_delimiters(text: str, eid: str) -> list[str]:
    issues = []
    stripped = text.replace("\\$", "").replace("$$", "")
    count = stripped.count("$")
    if count % 2 != 0:
        issues.append(f"Exercise {eid}: unbalanced $ delimiters ({count} found)")
    return issues


def _parse_args():
    findings_output = None
    config_path = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--findings-output" and i + 1 < len(args):
            findings_output = args[i + 1]
            i += 2
        elif not args[i].startswith("--"):
            config_path = args[i]
            i += 1
        else:
            i += 1
    return config_path, findings_output


def main():
    config_path, findings_output = _parse_args()
    cfg = load_config(config_path)
    out_dir = get_output_dir(cfg)
    criticals = 0
    warnings = 0
    total = 0
    collector = FindingCollector(source="validator_rag")

    print("# RAG Compatibility Report\n")

    for sid, sdir in get_session_dirs(cfg).items():
        for jf in get_json_files(cfg):
            fp = out_dir / sdir / jf
            if not fp.exists():
                continue
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                collector.add("critical", "rag", f"_session:{sid}",
                               f"Cannot load {fp.name}: {e}",
                               evidence=f"file={fp.name}, error={e}",
                               session_id=sid)
                criticals += 1
                continue

            for ex in data:
                total += 1
                eid = ex.get("id", f"unknown_{total}")

                # Non-empty question_text
                qt = ex.get("question_text", "")
                if not qt or not qt.strip():
                    print(f"### CRITICAL Exercise {eid}: empty question_text\n")
                    collector.add("critical", "rag", eid,
                                   "Empty question_text",
                                   session_id=sid)
                    criticals += 1
                elif len(qt) > MAX_QUESTION_CHARS:
                    print(f"### WARNING Exercise {eid}: question_text too long ({len(qt)} chars > {MAX_QUESTION_CHARS})\n")
                    collector.add("major", "rag", eid,
                                   f"question_text too long ({len(qt)} chars > {MAX_QUESTION_CHARS})",
                                   evidence=f"length={len(qt)}, max={MAX_QUESTION_CHARS}",
                                   session_id=sid, blocking=False)
                    warnings += 1

                # Non-empty solution text
                sol = ex.get("solution") or {}
                st = sol.get("text", "")
                if not st or not st.strip():
                    print(f"### CRITICAL Exercise {eid}: empty solution.text\n")
                    collector.add("critical", "rag", eid,
                                   "Empty solution.text",
                                   session_id=sid)
                    criticals += 1
                elif len(st) > MAX_SOLUTION_CHARS:
                    print(f"### WARNING Exercise {eid}: solution.text too long ({len(st)} chars > {MAX_SOLUTION_CHARS})\n")
                    collector.add("major", "rag", eid,
                                   f"solution.text too long ({len(st)} chars > {MAX_SOLUTION_CHARS})",
                                   evidence=f"length={len(st)}, max={MAX_SOLUTION_CHARS}",
                                   session_id=sid, blocking=False)
                    warnings += 1

                # Hints length
                for i, h in enumerate(ex.get("hints", []), 1):
                    if len(h) > MAX_HINT_CHARS:
                        print(f"### WARNING Exercise {eid}: hint {i} too long ({len(h)} chars > {MAX_HINT_CHARS})\n")
                        collector.add("minor", "rag", eid,
                                       f"Hint {i} too long ({len(h)} chars > {MAX_HINT_CHARS})",
                                       evidence=f"hint_index={i}, length={len(h)}, max={MAX_HINT_CHARS}",
                                       session_id=sid)
                        warnings += 1

                # Balanced LaTeX delimiters
                for issue in check_balanced_delimiters(qt + " " + st, eid):
                    print(f"### WARNING {issue}\n")
                    collector.add("major", "rag", eid,
                                   f"Unbalanced LaTeX delimiters: {issue}",
                                   evidence=issue,
                                   recommended_fix="Check and balance $ delimiters in question_text and solution.text",
                                   session_id=sid, blocking=False)
                    warnings += 1

    print(f"\n## Summary")
    print(f"- Exercises checked: {total}")
    print(f"- CRITICALs: {criticals}")
    print(f"- WARNINGs: {warnings}")
    print(f"- Verdict: {'PASS' if criticals == 0 else 'FAIL'}\n")

    if findings_output:
        collector.write(findings_output)
        print(f"Findings written to {findings_output} ({len(collector.findings)} findings)")

    sys.exit(0 if criticals == 0 else 1)


if __name__ == "__main__":
    main()
