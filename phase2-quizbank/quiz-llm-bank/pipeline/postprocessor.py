#!/usr/bin/env python3
"""Post-process exercises: fill related_exercises based on shared topics.

Deterministic, pure Python — no CLI calls. Runs after assembly.
Links exercises within the same language based on topic overlap.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import load_config, get_session_path


def compute_related(exercises: list[dict], max_related: int = 3) -> list[dict]:
    """Fill related_exercises for each exercise based on shared topics.

    Links within the same language only. Picks the top max_related
    exercises by topic overlap count (ties broken by ID for determinism).
    """
    # Build topic → exercise ID index
    topic_index: dict[str, list[str]] = defaultdict(list)
    ex_by_id: dict[str, dict] = {}

    for ex in exercises:
        ex_id = ex["id"]
        ex_by_id[ex_id] = ex
        for topic in ex.get("topics", []):
            topic_index[topic].append(ex_id)

    # Compute overlap scores
    for ex in exercises:
        ex_id = ex["id"]
        ex_topics = set(ex.get("topics", []))
        if not ex_topics:
            ex["related_exercises"] = []
            continue

        # Count overlap with every other exercise
        overlap_counts: dict[str, int] = defaultdict(int)
        for topic in ex_topics:
            for other_id in topic_index[topic]:
                if other_id != ex_id:
                    overlap_counts[other_id] += 1

        # Sort by overlap (desc), then by ID (asc) for determinism
        ranked = sorted(
            overlap_counts.items(),
            key=lambda x: (-x[1], x[0]),
        )

        ex["related_exercises"] = [oid for oid, _ in ranked[:max_related]]

    return exercises


def normalize_topics(exercises: list[dict], alias_map: dict[str, str]) -> list[dict]:
    """Remap exercise topics using an alias map.

    alias_map: {"old_topic": "canonical_topic", ...}
    Performs exact-match replacement. Logs each change.
    Returns the (mutated) exercises list.
    """
    if not alias_map:
        return exercises
    for ex in exercises:
        topics = ex.get("topics", [])
        new_topics = []
        seen: set[str] = set()
        for t in topics:
            canonical = alias_map.get(t, t)
            if canonical != t:
                print(f"  Topic alias: {ex.get('id', '?')}: '{t}' → '{canonical}'")
            if canonical not in seen:
                new_topics.append(canonical)
                seen.add(canonical)
        ex["topics"] = new_topics
    return exercises


def flag_unmappable_topics(exercises: list[dict], cfg: dict) -> list[str]:
    """Flag exercise topics not in any session's configured topics list.

    Returns list of warning strings (caller decides what to do with them).
    """
    all_configured: set[str] = set()
    for s in cfg["sessions"]:
        all_configured.update(s.get("topics", []))
    alias_map = cfg.get("topic_aliases", {})
    all_configured.update(alias_map.values())

    warnings: list[str] = []
    for ex in exercises:
        for t in ex.get("topics", []):
            if t not in all_configured:
                warnings.append(
                    f"Exercise {ex.get('id', '?')}: topic '{t}' not in any session's topics"
                )
    return warnings


def remap_exercise_ids(exercises: list[dict], id_map: dict[str, str]) -> list[dict]:
    """Remap exercise IDs and all cross-references using id_map.

    Updates: id, twin_id, prerequisites, related_exercises.
    Raises ValueError if id_map has many-to-one mappings (would create duplicates).
    Returns the (mutated) exercises list.
    """
    if not id_map:
        return exercises
    # Guard against many-to-one collisions
    target_ids = list(id_map.values())
    if len(target_ids) != len(set(target_ids)):
        dupes = [v for v in set(target_ids) if target_ids.count(v) > 1]
        raise ValueError(f"id_map has many-to-one collisions: {dupes}")
    for ex in exercises:
        old_id = ex.get("id", "")
        if old_id in id_map:
            ex["id"] = id_map[old_id]

        if ex.get("twin_id") in id_map:
            ex["twin_id"] = id_map[ex["twin_id"]]

        if "prerequisites" in ex and isinstance(ex["prerequisites"], list):
            ex["prerequisites"] = [
                id_map.get(p, p) for p in ex["prerequisites"]
            ]

        if "related_exercises" in ex and isinstance(ex["related_exercises"], list):
            ex["related_exercises"] = [
                id_map.get(r, r) for r in ex["related_exercises"]
            ]
    return exercises


def postprocess_session(cfg: dict, session: dict, language: str) -> int:
    """Post-process a single session/language file. Returns exercise count."""
    session_path = get_session_path(cfg, session["id"])
    lang_upper = language.upper()
    json_path = session_path / f"exercises_{lang_upper}.json"

    if not json_path.exists():
        print(f"  SKIP {json_path.name} — file not found")
        return 0

    exercises = json.loads(json_path.read_text(encoding="utf-8"))
    exercises = compute_related(exercises)

    json_path.write_text(
        json.dumps(exercises, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return len(exercises)


def postprocess_all(cfg: dict):
    """Post-process all sessions and languages."""
    for session in cfg["sessions"]:
        for lang in cfg["languages"]:
            count = postprocess_session(cfg, session, lang)
            if count > 0:
                print(f"  {session['id']} / {lang.upper()}: {count} exercises updated")


def main():
    cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else None)
    print("Post-processing: filling related_exercises...")
    postprocess_all(cfg)
    print("Done.")


if __name__ == "__main__":
    main()
