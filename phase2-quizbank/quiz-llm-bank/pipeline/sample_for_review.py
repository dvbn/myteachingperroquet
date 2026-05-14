#!/usr/bin/env python3
"""Stratified sampler for human expert review (Phase 6, optional).

Config-driven version: reads paths from course_config.json.

Selects exercises for SME review based on:
- 100% of WARNING-flagged exercises
- 100% of HARD exercises
- 100% of exercises where audit agents disagreed
- Stratified random >=20% of remaining (balanced by session/type/difficulty)

Output: output/<course_id>/validation/review_queue.json
"""

import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import load_config, get_output_dir, get_session_dirs, get_json_files, get_validation_dir


def load_exercises(cfg: dict) -> list:
    """Load all exercises from the bank."""
    out_dir = get_output_dir(cfg)
    exercises = []
    for sid, sdir in get_session_dirs(cfg).items():
        for jf in get_json_files(cfg):
            fp = out_dir / sdir / jf
            if fp.exists():
                with open(fp, encoding="utf-8") as f:
                    exercises.extend(json.load(f))
    return exercises


def load_audit_findings(validation_dir: Path) -> dict:
    """Parse audit findings JSON files for flagged IDs and cross-agent
    disagreements.

    Looks at both audit pipelines:
      - validation_dir/claude_audit/claude_audit_<sid>_findings.json
      - validation_dir/codex_audit/codex_audit_<sid>_findings.json

    Falls back to scanning the markdown reports for ``### [SEV] Exercise <id>``
    headers if the structured findings JSON files are missing (older runs).

    Returns ``{"flagged": set[str], "disagreements": set[str]}``.
    """
    flagged: set[str] = set()
    findings_by_exercise: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )

    if not validation_dir.is_dir():
        return {"flagged": flagged, "disagreements": set()}

    BLOCKING_SEVERITIES = {"critical", "major", "warning"}

    for sub in ("claude_audit", "codex_audit"):
        audit_dir = validation_dir / sub
        if not audit_dir.is_dir():
            continue
        agent = sub.split("_")[0]

        # Preferred: structured findings JSON
        for j in audit_dir.glob("*_findings.json"):
            try:
                payload = json.loads(j.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            entries = (
                payload.get("findings", payload) if isinstance(payload, dict) else payload
            )
            for f in entries:
                sev = (f.get("severity") or "").lower()
                eid = f.get("exercise_id")
                if eid and sev in BLOCKING_SEVERITIES:
                    flagged.add(eid)
                    findings_by_exercise[eid][agent].append(sev)

        # Fallback: markdown headers (covers any run that didn't emit findings JSON)
        for md_file in audit_dir.glob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            for match in re.finditer(
                r"###\s*\[?(CRITICAL|WARNING|MAJOR)\]?\s+Exercise\s+(\S+)", text
            ):
                severity, ex_id = match.groups()
                flagged.add(ex_id)
                findings_by_exercise[ex_id][agent].append(severity.lower())

    disagreements = set()
    for ex_id, agent_findings in findings_by_exercise.items():
        if len(agent_findings) > 1:
            severities: set[str] = set()
            for sev_list in agent_findings.values():
                severities.update(sev_list)
            if len(severities) > 1:
                disagreements.add(ex_id)

    return {"flagged": flagged, "disagreements": disagreements}


def stratified_sample(exercises: list, mandatory_ids: set, rate: float = 0.2) -> list:
    """Select stratified random sample of remaining exercises."""
    remaining = [e for e in exercises if e["id"] not in mandatory_ids]

    strata = defaultdict(list)
    for ex in remaining:
        key = (ex["session"], ex["question_type"], ex["difficulty"])
        strata[key].append(ex)

    sampled = []
    for key, group in strata.items():
        n = max(1, int(len(group) * rate))
        sampled.extend(random.sample(group, min(n, len(group))))

    return sampled


def main():
    cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else None)
    val_dir = get_validation_dir(cfg)
    output_path = val_dir / "review_queue.json"

    exercises = load_exercises(cfg)
    if not exercises:
        print("ERROR: No exercises loaded", file=sys.stderr)
        sys.exit(1)

    audit_info = load_audit_findings(val_dir)
    mandatory_ids = set()

    # 100% of WARNING-flagged
    mandatory_ids.update(audit_info["flagged"])

    # 100% of highest-difficulty exercises
    difficulty_levels = list(cfg.get("difficulty_distribution", {"HARD": 0.25}).keys())
    highest_difficulty = difficulty_levels[-1] if difficulty_levels else "HARD"
    for ex in exercises:
        if ex["difficulty"] == highest_difficulty:
            mandatory_ids.add(ex["id"])

    # 100% of disagreements
    mandatory_ids.update(audit_info["disagreements"])

    # Stratified random >=20% of remaining
    sampled = stratified_sample(exercises, mandatory_ids, rate=0.2)
    sampled_ids = {ex["id"] for ex in sampled}

    # Build queue
    queue = []
    for ex in exercises:
        if ex["id"] in mandatory_ids:
            reasons = []
            if ex["difficulty"] == highest_difficulty:
                reasons.append(f"highest_difficulty ({highest_difficulty})")
            if ex["id"] in audit_info["flagged"]:
                reasons.append("audit_flagged")
            if ex["id"] in audit_info["disagreements"]:
                reasons.append("agent_disagreement")
            queue.append({
                "id": ex["id"],
                "session": ex["session"],
                "type": ex["question_type"],
                "difficulty": ex["difficulty"],
                "language": ex["language"],
                "reason": ", ".join(reasons),
                "priority": "mandatory",
            })
        elif ex["id"] in sampled_ids:
            queue.append({
                "id": ex["id"],
                "session": ex["session"],
                "type": ex["question_type"],
                "difficulty": ex["difficulty"],
                "language": ex["language"],
                "reason": "stratified_sample",
                "priority": "sampled",
            })

    queue.sort(key=lambda x: (0 if x["priority"] == "mandatory" else 1, x["session"], x["id"]))

    val_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

    total = len(exercises)
    mandatory = len([q for q in queue if q["priority"] == "mandatory"])
    sampled_count = len([q for q in queue if q["priority"] == "sampled"])
    coverage = len(queue) / total * 100 if total > 0 else 0

    print(f"Review queue generated: {output_path}")
    print(f"  Total exercises: {total}")
    print(f"  Mandatory review: {mandatory} ({highest_difficulty} + flagged + disagreements)")
    print(f"  Stratified sample: {sampled_count}")
    print(f"  Total in queue: {len(queue)} ({coverage:.1f}% coverage)")


if __name__ == "__main__":
    main()
