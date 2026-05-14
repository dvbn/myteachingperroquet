#!/usr/bin/env python3
"""Phase 2 validator: ID integrity, cross-references, prerequisites.

Checks:
- ID uniqueness across the entire bank
- ID components match exercise fields (session, language, type)
- twin_id bidirectionality
- related_exercises reference existing IDs in same language
- prerequisites reference only earlier sessions
- Sequential numbering within session/lang/type groups

Exit code 0 = PASS, 1 = FAIL.

Flags:
  --findings-output <path>  Write structured findings JSON alongside markdown.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config_loader import load_config, get_output_dir, get_session_dirs, get_json_files
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


def load_all(cfg, collector=None):
    """Load every exercise into a flat list, tagged with source file."""
    out_dir = get_output_dir(cfg)
    exercises = []
    for sid, sdir in get_session_dirs(cfg).items():
        for jf in get_json_files(cfg):
            fp = out_dir / sdir / jf
            if not fp.exists():
                continue
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                if collector:
                    collector.add("critical", "structure", f"_session:{sid}",
                                   f"Cannot load {fp.name}: {e}",
                                   evidence=f"file={fp.name}, error={e}",
                                   session_id=sid)
                continue
            for ex in data:
                ex["_src"] = str(fp)
                ex["_session_id"] = sid
                exercises.append(ex)
    return exercises


def _build_id_regex_with_groups(cfg: dict) -> re.Pattern | None:
    session_ids = [s["id"] for s in cfg["sessions"]]
    languages = [l.upper() for l in cfg["languages"]]
    ex_types = cfg["exercise_types"]

    session_alt = "|".join(re.escape(s) for s in session_ids)
    lang_alt = "|".join(re.escape(l) for l in languages)
    type_alt = "|".join(re.escape(t) for t in ex_types)

    for sep in ["_", "-", "."]:
        pat = (
            rf"^(?P<session>{session_alt}){re.escape(sep)}"
            rf"(?P<lang>{lang_alt}){re.escape(sep)}"
            rf"(?P<type>{type_alt}){re.escape(sep)}"
            rf"(?P<seq>\d+)$"
        )
        try:
            compiled = re.compile(pat)
            return compiled
        except re.error:
            continue
    return None


def main():
    config_path, findings_output = _parse_args()
    cfg = load_config(config_path)
    collector = FindingCollector(source="validator_structure")
    exercises = load_all(cfg, collector)
    id_pat = re.compile(cfg["id_regex"])
    session_order = {s["id"]: i for i, s in enumerate(cfg["sessions"])}
    session_ids = set(session_order.keys())
    all_ids = {}
    criticals = 0
    warnings = 0

    decompose_pat = _build_id_regex_with_groups(cfg)

    print("# Structure Validation Report\n")

    # Pass 1: collect all IDs, check uniqueness
    for ex in exercises:
        eid = ex.get("id", "")
        if eid in all_ids:
            print(f"### CRITICAL Duplicate ID: {eid}")
            print(f"- Found in: {ex['_src']} and {all_ids[eid]['_src']}\n")
            collector.add("critical", "structure", eid,
                           f"Duplicate ID: found in {ex['_src']} and {all_ids[eid]['_src']}",
                           evidence=f"files: {ex['_src']}, {all_ids[eid]['_src']}",
                           session_id=ex.get("_session_id"))
            criticals += 1
        all_ids[eid] = ex

    # Pass 2: validate each exercise
    for ex in exercises:
        eid = ex.get("id", "")
        sid = ex.get("_session_id")

        # ID pattern
        if not id_pat.match(eid):
            print(f"### CRITICAL Exercise {eid}: ID doesn't match pattern {cfg['id_regex']}\n")
            collector.add("critical", "structure", eid,
                           f"ID doesn't match pattern {cfg['id_regex']}",
                           evidence=f"id={eid}, pattern={cfg['id_regex']}",
                           session_id=sid)
            criticals += 1
            continue

        # ID components vs fields
        if decompose_pat:
            m = decompose_pat.match(eid)
            if m:
                id_session = m.group("session")
                id_lang = m.group("lang").lower()
                id_type = m.group("type")

                if id_session != ex.get("session", ""):
                    print(f"### CRITICAL Exercise {eid}: ID session '{id_session}' != field session '{ex.get('session')}'")
                    collector.add("critical", "structure", eid,
                                   f"ID session component '{id_session}' != field session '{ex.get('session')}'",
                                   evidence=f"id_session={id_session}, field_session={ex.get('session')}",
                                   session_id=sid)
                    criticals += 1

                if id_lang != ex.get("language", ""):
                    print(f"### CRITICAL Exercise {eid}: ID lang '{id_lang}' != field language '{ex.get('language')}'")
                    collector.add("critical", "structure", eid,
                                   f"ID language component '{id_lang}' != field language '{ex.get('language')}'",
                                   evidence=f"id_lang={id_lang}, field_language={ex.get('language')}",
                                   session_id=sid)
                    criticals += 1

                if id_type != ex.get("question_type", ""):
                    print(f"### CRITICAL Exercise {eid}: ID type '{id_type}' != field question_type '{ex.get('question_type')}'")
                    collector.add("critical", "structure", eid,
                                   f"ID type component '{id_type}' != field question_type '{ex.get('question_type')}'",
                                   evidence=f"id_type={id_type}, field_question_type={ex.get('question_type')}",
                                   session_id=sid)
                    criticals += 1

        # Twin bidirectionality
        twin = ex.get("twin_id", "")
        if twin:
            if twin not in all_ids:
                print(f"### CRITICAL Exercise {eid}: twin_id '{twin}' does not exist\n")
                collector.add("critical", "structure", eid,
                               f"twin_id '{twin}' does not exist",
                               evidence=f"twin_id={twin}",
                               session_id=sid)
                criticals += 1
            elif all_ids[twin].get("twin_id") != eid:
                print(f"### CRITICAL Exercise {eid}: twin link not bidirectional (twin {twin} points to '{all_ids[twin].get('twin_id')}')\n")
                collector.add("critical", "structure", eid,
                               f"Twin link not bidirectional: twin {twin} points to '{all_ids[twin].get('twin_id')}' instead of '{eid}'",
                               evidence=f"twin={twin}, twin.twin_id={all_ids[twin].get('twin_id')}",
                               session_id=sid)
                criticals += 1

        # related_exercises: must exist and be same language
        for rel in ex.get("related_exercises", []):
            if rel not in all_ids:
                print(f"### CRITICAL Exercise {eid}: related_exercises '{rel}' does not exist\n")
                collector.add("critical", "structure", eid,
                               f"related_exercises reference '{rel}' does not exist",
                               evidence=f"related_exercises contains '{rel}'",
                               session_id=sid)
                criticals += 1
            elif all_ids[rel].get("language") != ex.get("language"):
                print(f"### WARNING Exercise {eid}: related '{rel}' is in different language\n")
                collector.add("minor", "structure", eid,
                               f"related_exercises '{rel}' is in different language ({all_ids[rel].get('language')} vs {ex.get('language')})",
                               session_id=sid)
                warnings += 1

        # Prerequisites: must reference only earlier sessions
        ex_session_idx = session_order.get(ex.get("session", ""), 999)
        for prereq in ex.get("prerequisites", []):
            prereq_session = None
            for s_id in session_ids:
                if prereq.startswith(s_id + "_") or prereq == s_id:
                    prereq_session = s_id
                    break
            if prereq_session:
                prereq_idx = session_order.get(prereq_session, -1)
                if prereq_idx >= ex_session_idx:
                    print(f"### WARNING Exercise {eid}: prerequisite '{prereq}' references same/later session\n")
                    collector.add("minor", "structure", eid,
                                   f"Prerequisite '{prereq}' references same or later session",
                                   evidence=f"prerequisite session={prereq_session}, exercise session={ex.get('session')}",
                                   session_id=sid)
                    warnings += 1

    # Pass 3: check sequential numbering within groups
    groups = defaultdict(list)
    for ex in exercises:
        eid = ex.get("id", "")
        if not id_pat.match(eid):
            continue
        if decompose_pat:
            dm = decompose_pat.match(eid)
            if dm:
                prefix = f"{dm.group('session')}_{dm.group('lang')}_{dm.group('type')}"
                seq = int(dm.group("seq"))
                groups[prefix].append(seq)
                continue
        for sep in ["_", "-", "."]:
            parts = eid.rsplit(sep, 1)
            if len(parts) == 2 and parts[1].isdigit():
                groups[parts[0]].append(int(parts[1]))
                break

    for prefix, seqs in groups.items():
        seqs.sort()
        expected = list(range(1, len(seqs) + 1))
        if seqs != expected:
            print(f"### WARNING Group {prefix}: non-sequential IDs (found {seqs}, expected {expected})\n")
            collector.add("minor", "structure", f"_global",
                           f"Group {prefix}: non-sequential IDs (found {seqs}, expected {expected})",
                           evidence=f"actual={seqs}, expected={expected}")
            warnings += 1

    print(f"\n## Summary")
    print(f"- Exercises checked: {len(exercises)}")
    print(f"- Unique IDs: {len(all_ids)}")
    print(f"- CRITICALs: {criticals}")
    print(f"- WARNINGs: {warnings}")
    print(f"- Verdict: {'PASS' if criticals == 0 else 'FAIL'}\n")

    if findings_output:
        collector.write(findings_output)
        print(f"Findings written to {findings_output} ({len(collector.findings)} findings)")

    sys.exit(0 if criticals == 0 else 1)


if __name__ == "__main__":
    main()
