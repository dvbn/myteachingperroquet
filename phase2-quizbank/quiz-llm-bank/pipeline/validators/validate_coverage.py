#!/usr/bin/env python3
"""Phase 2 validator: exercise counts and distribution.

Checks:
- Total exercise count per session matches config
- Type distribution per session matches config (if specified)
- Difficulty distribution across bank approximately matches config
- Cross-language balance per session

Exit code 0 = PASS, 1 = FAIL.

Flags:
  --findings-output <path>  Write structured findings JSON alongside markdown.
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config_loader import (
    load_config, get_output_dir, get_session_dirs, get_json_files,
    get_languages, get_primary_language,
)
from findings_io import FindingCollector


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
    languages = get_languages(cfg)
    primary_lang = get_primary_language(cfg).upper()
    tool = cfg.get("software_tool", "").lower()
    criticals = 0
    warnings = 0
    collector = FindingCollector(source="validator_coverage")

    print("# Coverage Validation Report\n")

    all_difficulties = Counter()
    total_exercises = 0

    for session in cfg["sessions"]:
        sid = session["id"]
        sdir = session["dir"]
        expected_count = session["exercise_count"]
        type_dist = session.get("type_distribution", {})

        lang_counts = {}
        type_counts = Counter()
        for lang in languages:
            lang_upper = lang.upper()
            fp = out_dir / sdir / f"exercises_{lang_upper}.json"
            count = 0
            if fp.exists():
                try:
                    with open(fp, encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    collector.add("critical", "coverage", f"_session:{sid}",
                                   f"Cannot load {fp.name}: {e}",
                                   evidence=f"file={fp.name}, error={e}",
                                   session_id=sid)
                    criticals += 1
                    lang_counts[lang_upper] = 0
                    continue
                count = len(data)
                for ex in data:
                    if lang_upper == primary_lang:
                        type_counts[ex.get("question_type", "UNKNOWN")] += 1
                        all_difficulties[ex.get("difficulty", "UNKNOWN")] += 1
                        total_exercises += 1
            lang_counts[lang_upper] = count

            if tool:
                tool_fp = out_dir / sdir / f"{tool}_{lang_upper}.json"
                if tool_fp.exists():
                    try:
                        with open(tool_fp, encoding="utf-8") as f:
                            tool_data = json.load(f)
                    except (json.JSONDecodeError, OSError):
                        continue
                    lang_counts[lang_upper] += len(tool_data)
                    if lang_upper == primary_lang:
                        for ex in tool_data:
                            type_counts[ex.get("question_type", tool.upper())] += 1
                            all_difficulties[ex.get("difficulty", "UNKNOWN")] += 1
                            total_exercises += 1

        # Check primary language count
        primary_count = lang_counts.get(primary_lang, 0)
        if primary_count != expected_count:
            print(f"### WARNING {sid}: {primary_lang} count {primary_count} != expected {expected_count}\n")
            collector.add("major", "coverage", f"_session:{sid}",
                           f"{primary_lang} exercise count {primary_count} != expected {expected_count}",
                           evidence=f"actual={primary_count}, expected={expected_count}",
                           session_id=sid, blocking=False)
            warnings += 1

        # Check cross-language balance
        counts_list = list(lang_counts.values())
        if len(set(counts_list)) > 1:
            detail = ", ".join(f"{k}={v}" for k, v in lang_counts.items())
            print(f"### CRITICAL {sid}: language count imbalance ({detail})\n")
            collector.add("critical", "coverage", f"_session:{sid}",
                           f"Language count imbalance: {detail}",
                           evidence=detail, session_id=sid)
            criticals += 1

        # Check type distribution
        if type_dist:
            for qtype, expected_n in type_dist.items():
                actual_n = type_counts.get(qtype, 0)
                if actual_n != expected_n:
                    print(f"### WARNING {sid}: type {qtype} count {actual_n} != expected {expected_n}\n")
                    collector.add("major", "coverage", f"_session:{sid}",
                                   f"Type {qtype} count {actual_n} != expected {expected_n}",
                                   evidence=f"type={qtype}, actual={actual_n}, expected={expected_n}",
                                   session_id=sid, blocking=False)
                    warnings += 1

    # Global difficulty distribution
    if total_exercises > 0:
        print("## Difficulty Distribution\n")
        target = cfg["difficulty_distribution"]
        for diff, target_pct in target.items():
            actual_pct = all_difficulties.get(diff, 0) / total_exercises
            print(f"- {diff}: {all_difficulties.get(diff, 0)}/{total_exercises} ({actual_pct:.1%}) — target {target_pct:.0%}")
            if abs(actual_pct - target_pct) > 0.10:
                print(f"  WARNING: off by {abs(actual_pct - target_pct):.0%}\n")
                collector.add("major", "coverage", "_global",
                               f"Difficulty '{diff}' distribution off: {actual_pct:.1%} vs target {target_pct:.0%}",
                               evidence=f"actual={actual_pct:.3f}, target={target_pct:.3f}, delta={abs(actual_pct - target_pct):.3f}",
                               blocking=False)
                warnings += 1
        print()

    print(f"\n## Summary")
    print(f"- Total exercises ({primary_lang}): {total_exercises}")
    print(f"- Sessions checked: {len(cfg['sessions'])}")
    print(f"- CRITICALs: {criticals}")
    print(f"- WARNINGs: {warnings}")
    print(f"- Verdict: {'PASS' if criticals == 0 else 'FAIL'}\n")

    if findings_output:
        collector.write(findings_output)
        print(f"Findings written to {findings_output} ({len(collector.findings)} findings)")

    sys.exit(0 if criticals == 0 else 1)


if __name__ == "__main__":
    main()
