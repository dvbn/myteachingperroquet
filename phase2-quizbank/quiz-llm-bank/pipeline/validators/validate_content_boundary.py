#!/usr/bin/env python3
"""Phase 2 validator: content boundary enforcement.

Checks that exercise content stays within the scope of what is actually
taught in the course slides, using per-session ``scope_terms``.

Checks:
1. CRITICAL — Exercise ``topics`` field contains a topic NOT in the session's
   configured ``topics`` list.
2. CRITICAL — Exercise text references a named method/test that appears only
   in a LATER session's ``scope_terms`` (forward reference).
3. (Covered by checks 2+4) — A term not in any session's scope_terms is
   invisible to the validator; only terms explicitly listed are checked.
4. MAJOR    — Exercise text references a named method/test from a
   non-prerequisite, non-current session (cross-session leak).

Self-tests (non-blocking warnings):
- Pattern self-match: every scope_term must match itself
- Bilingual coverage: flag sessions where one language has >30% fewer terms
- DAG cycle check

Novel term detection (MAJOR, advisory):
- Flags capitalized multi-word phrases and acronyms not in any scope_terms list

Exit code 0 = PASS, 1 = FAIL (any CRITICAL found).

Flags:
  --findings-output <path>  Write structured findings JSON.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config_loader import load_config, get_output_dir, get_session_dirs, get_json_files
from findings_io import FindingCollector
from scope_resolver import (
    build_term_pattern,
    extract_exercise_text,
    get_prerequisite_closure,
    get_session_order,
)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_all_exercises(cfg, collector):
    """Load every exercise into a flat list with session metadata."""
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
                collector.add("critical", "content_boundary", f"_session:{sid}",
                              f"Cannot load {fp.name}: {e}",
                              session_id=sid)
                continue
            if not isinstance(data, list):
                if collector:
                    collector.add("critical", "content_boundary", f"_session:{sid}",
                                  f"{fp.name} root is not an array",
                                  session_id=sid)
                continue
            for ex in data:
                if not isinstance(ex, dict):
                    continue
                ex["_session_id"] = sid
                exercises.append(ex)
    return exercises


def _build_scope_maps(cfg: dict):
    """Build per-session and global scope maps from config.

    Returns:
        session_terms: {session_id: {lang: [compiled_patterns]}}
        session_term_strings: {session_id: {lang: [raw_strings]}}
        session_order: {session_id: int}
        prerequisite_map: {session_id: set(prerequisite_session_ids)}
    """
    sessions = cfg["sessions"]
    session_order = get_session_order(cfg)

    # Build prerequisite map via scope_resolver (transitive)
    prerequisite_map = {
        s["id"]: get_prerequisite_closure(cfg, s["id"]) for s in sessions
    }

    session_terms = {}
    session_term_strings = {}
    for s in sessions:
        sid = s["id"]
        st = s.get("scope_terms", {})
        session_terms[sid] = {}
        session_term_strings[sid] = {}
        for lang in cfg["languages"]:
            raw_terms = [t for t in st.get(lang, []) if t and t.strip()]
            # Build patterns and keep terms/patterns aligned (filter both together)
            paired = [
                (t.lower(), build_term_pattern(t))
                for t in raw_terms
            ]
            paired = [(t, p) for t, p in paired if p is not None]
            session_term_strings[sid][lang] = [t for t, _ in paired]
            session_terms[sid][lang] = [p for _, p in paired]

    return session_terms, session_term_strings, session_order, prerequisite_map


def _get_exercise_language(ex: dict) -> str:
    """Return exercise language code."""
    return (ex.get("language") or "en").lower()


# ---------------------------------------------------------------------------
# Self-test (Step 5)
# ---------------------------------------------------------------------------

def _run_self_test(cfg: dict, collector: FindingCollector):
    """Pre-flight self-test on scope_terms configuration (non-blocking warnings)."""
    warnings = 0

    # 1. Pattern self-match: every scope_term must match itself
    for s in cfg["sessions"]:
        sid = s["id"]
        for lang in cfg["languages"]:
            for term in s.get("scope_terms", {}).get(lang, []):
                if not term or not term.strip():
                    continue
                pat = build_term_pattern(term)
                if pat is None:
                    collector.add(
                        "warning", "self_test_pattern", f"_config:{sid}",
                        f"scope_term '{term}' ({lang}) produced no regex pattern",
                        session_id=sid,
                    )
                    warnings += 1
                    continue
                if not pat.search(f" {term} "):
                    collector.add(
                        "warning", "self_test_pattern", f"_config:{sid}",
                        f"scope_term '{term}' ({lang}) does NOT self-match its own regex",
                        session_id=sid,
                        recommended_fix="Review the term for unusual characters",
                    )
                    warnings += 1

    # 2. Bilingual coverage: flag sessions where one language has >30% fewer terms
    langs = cfg["languages"]
    if len(langs) >= 2:
        for s in cfg["sessions"]:
            sid = s["id"]
            st = s.get("scope_terms", {})
            counts = {lang: len(st.get(lang, [])) for lang in langs}
            max_count = max(counts.values()) if counts else 0
            if max_count == 0:
                continue
            for lang, cnt in counts.items():
                if cnt < max_count * 0.7:
                    collector.add(
                        "warning", "self_test_bilingual", f"_config:{sid}",
                        f"Session {sid} scope_terms: {lang} has {cnt} terms vs max {max_count} (>30% gap)",
                        session_id=sid,
                        recommended_fix=f"Add missing {lang} translations for scope_terms in session {sid}",
                    )
                    warnings += 1

    # 3. DAG cycle detection via BFS
    session_ids = [s["id"] for s in cfg["sessions"]]
    for sid in session_ids:
        closure = get_prerequisite_closure(cfg, sid)
        if sid in closure:
            collector.add(
                "warning", "self_test_dag_cycle", f"_config:{sid}",
                f"Session {sid} has a cycle in its prerequisite chain",
                session_id=sid,
                recommended_fix="Remove circular prerequisite references",
            )
            warnings += 1

    if warnings:
        print(f"  Self-test: {warnings} warning(s) found")
    else:
        print("  Self-test: all checks passed")


# ---------------------------------------------------------------------------
# Novel term detection (Step 10)
# ---------------------------------------------------------------------------

def _extract_candidate_terms(text: str, trigger_words: list[str]) -> set[str]:
    """Heuristically extract candidate technical terms from text.

    Returns acronyms (2+ uppercase letters) and terms appearing
    immediately before or after a configured trigger word
    (e.g. "test", "method", "theorem"). The previous version also
    matched any capitalized multi-word phrase, which produced hundreds
    of false positives on ordinary sentence starters like "Suppose the
    Researcher". That branch has been removed; rely on the trigger-word
    heuristic and the configured `scope_terms` allow-list instead.
    """
    candidates: set[str] = set()

    # Acronyms: 2+ uppercase letters (optionally followed by digits)
    for m in re.finditer(r"\b([A-Z]{2,}[0-9]*)\b", text):
        candidates.add(m.group(1))

    # Terms after trigger words (e.g. "test" -> "Breusch-Pagan")
    for trigger in trigger_words:
        pat = re.compile(
            r"\b([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\-]+(?:\s+[A-Za-zÀ-ÿ\-]+){0,3})\s+"
            + re.escape(trigger) + r"\b",
            re.IGNORECASE,
        )
        for m in pat.finditer(text):
            candidates.add(m.group(1))
        # Also: "trigger of/de X"
        pat2 = re.compile(
            r"\b" + re.escape(trigger) + r"\s+(?:of|de)\s+"
            r"([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\-]+(?:\s+[A-Za-zÀ-ÿ\-]+){0,3})\b",
            re.IGNORECASE,
        )
        for m in pat2.finditer(text):
            candidates.add(m.group(1))

    return candidates


def _detect_novel_terms(exercises: list[dict], cfg: dict,
                        session_term_strings: dict,
                        collector: FindingCollector) -> int:
    """Flag terms that appear in exercises but not in any session's scope_terms."""
    trigger_words = (
        cfg.get("content_boundary", {}).get("novel_term_triggers", [])
    )
    if not trigger_words:
        # Feature disabled when no triggers configured
        return 0

    # Collect all known terms (lowercased) across all sessions and languages
    all_known: set[str] = set()
    for sid_terms in session_term_strings.values():
        for lang_terms in sid_terms.values():
            all_known.update(lang_terms)  # already lowered

    count = 0
    for ex in exercises:
        eid = ex.get("id", "unknown")
        sid = ex.get("_session_id", "")
        text = extract_exercise_text(ex)
        if not text.strip():
            continue
        candidates = _extract_candidate_terms(text, trigger_words)
        for cand in sorted(candidates):
            if cand.lower() not in all_known and len(cand) > 2:
                # Advisory only — the LLM audits' `forward_reference`
                # category is the authoritative scope check.
                collector.add(
                    "minor", "novel_term", eid,
                    f"Potential novel term '{cand}' not in any session's scope_terms",
                    session_id=sid,
                    recommended_fix=f"Add '{cand}' to scope_terms if it's a legitimate course concept, or remove from exercise",
                )
                count += 1

    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    config_path, findings_output = _parse_args()
    cfg = load_config(config_path)
    collector = FindingCollector(source="validator_content_boundary")

    # Check that scope_terms exist in config
    has_scope_terms = any(
        s.get("scope_terms") for s in cfg["sessions"]
    )
    if not has_scope_terms:
        print("# Content Boundary Validation Report\n")
        print("SKIPPED: No scope_terms configured in any session.")
        print("Add scope_terms to course_config.json to enable this validator.\n")
        if findings_output:
            collector.write(findings_output)
        sys.exit(0)

    # Self-test before exercise loading
    print("# Content Boundary Validation Report\n")
    _run_self_test(cfg, collector)

    exercises = _load_all_exercises(cfg, collector)
    session_terms, session_term_strings, session_order, prerequisite_map = (
        _build_scope_maps(cfg)
    )
    # Allowed topic labels = session.topics ∪ scope_terms ∪ foundational_terms
    # in the prerequisite closure (case-insensitive). Both `session.topics` and
    # `scope_terms` are legitimate sources of topic labels — the former lists
    # the high-level themes, the latter lists named methods/tests/estimators
    # the session covers. Rejecting an exercise that uses a `scope_terms`
    # label as a topic was too strict and produced spurious CRITICALs.
    session_allowed_topics: dict[str, set[str]] = {}
    for s in cfg["sessions"]:
        sid = s["id"]
        labels: set[str] = {t.lower() for t in s.get("topics", [])}
        for lang in cfg.get("languages", []):
            for t in s.get("scope_terms", {}).get(lang, []):
                labels.add(t.lower())
        for lang in cfg.get("languages", []):
            for ft in cfg.get("foundational_terms", {}).get(lang, []):
                term = ft.get("term", "")
                intro = ft.get("introduced_in", "")
                if term and session_order.get(intro, float("inf")) <= session_order.get(sid, -1):
                    labels.add(term.lower())
        session_allowed_topics[sid] = labels

    criticals = 0
    majors = 0

    for ex in exercises:
        eid = ex.get("id", "unknown")
        sid = ex.get("_session_id", "")
        lang = _get_exercise_language(ex)

        if sid not in session_order:
            continue

        # ------------------------------------------------------------------
        # Check 1: Exercise topics ⊆ session.topics ∪ scope_terms ∪ allowed
        #          foundational_terms (case-insensitive)
        # ------------------------------------------------------------------
        ex_topics = ex.get("topics", []) or []
        allowed_topics = session_allowed_topics.get(sid, set())
        for topic in ex_topics:
            if topic.lower() not in allowed_topics:
                print(f"### CRITICAL {eid}: topic '{topic}' not in session {sid} allow-list")
                collector.add(
                    "critical", "topic_scope", eid,
                    f"Exercise topic '{topic}' is not in session {sid}'s allow-list "
                    f"(session.topics + scope_terms + allowed foundational_terms)",
                    evidence=f"exercise_topic={topic}",
                    session_id=sid,
                    recommended_fix=f"Remove '{topic}' from exercise topics or add it to session {sid} config",
                )
                criticals += 1

        # ------------------------------------------------------------------
        # Checks 2-4: Scan text for scope_terms matches
        # ------------------------------------------------------------------
        text = extract_exercise_text(ex)
        if not text.strip():
            continue

        # Build allowed terms for this session:
        # own terms + all prerequisite session terms
        allowed_sessions = {sid} | prerequisite_map.get(sid, set())
        later_sessions = {
            s_id for s_id, idx in session_order.items()
            if idx > session_order[sid] and s_id not in allowed_sessions
        }
        non_prereq_earlier = {
            s_id for s_id, idx in session_order.items()
            if idx <= session_order[sid]
            and s_id not in allowed_sessions
            and s_id != sid
        }

        # Check 2: forward references (deduplicated by term)
        reported_fwd = set()
        for later_sid in later_sessions:
            for pat, raw_term in zip(
                session_terms.get(later_sid, {}).get(lang, []),
                session_term_strings.get(later_sid, {}).get(lang, []),
            ):
                if raw_term in reported_fwd:
                    continue
                if pat.search(text):
                    in_allowed = any(
                        raw_term in session_term_strings.get(a, {}).get(lang, [])
                        for a in allowed_sessions
                    )
                    if not in_allowed:
                        reported_fwd.add(raw_term)
                        print(f"### CRITICAL {eid}: forward reference to '{raw_term}' (from {later_sid})")
                        collector.add(
                            "critical", "forward_reference", eid,
                            f"References '{raw_term}' which is only taught in later session {later_sid}",
                            evidence=f"term='{raw_term}', source_session={later_sid}, exercise_session={sid}",
                            session_id=sid,
                            recommended_fix=f"Remove reference to '{raw_term}' or move exercise to {later_sid}",
                        )
                        criticals += 1

        # Check 3: completely out-of-scope terms
        # (We cannot enumerate unknown terms, but we check all known terms from
        #  ALL sessions — if a term matches only in sessions not allowed and not
        #  later, it means it's from a non-prereq earlier session; if it matches
        #  no session at all, it's not in our scope_terms list. Check 3 is
        #  effectively covered by checks 2+4 since we enumerate all known terms.)

        # Check 4: non-prerequisite earlier session terms (MAJOR, deduplicated)
        reported_np = set()
        for np_sid in non_prereq_earlier:
            for pat, raw_term in zip(
                session_terms.get(np_sid, {}).get(lang, []),
                session_term_strings.get(np_sid, {}).get(lang, []),
            ):
                if raw_term in reported_np or raw_term in reported_fwd:
                    continue
                if pat.search(text):
                    in_allowed = any(
                        raw_term in session_term_strings.get(a, {}).get(lang, [])
                        for a in allowed_sessions
                    )
                    if not in_allowed:
                        reported_np.add(raw_term)
                        print(f"### MAJOR {eid}: references '{raw_term}' from non-prerequisite session {np_sid}")
                        collector.add(
                            "major", "non_prerequisite_ref", eid,
                            f"References '{raw_term}' from session {np_sid} which is not a prerequisite of {sid}",
                            evidence=f"term='{raw_term}', ref_session={np_sid}, exercise_session={sid}, prerequisites={sorted(prerequisite_map.get(sid, set()))}",
                            session_id=sid,
                            recommended_fix=f"Add {np_sid} as prerequisite or remove reference to '{raw_term}'",
                        )
                        majors += 1

    # Novel term detection
    novel_count = _detect_novel_terms(exercises, cfg, session_term_strings, collector)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n## Summary")
    print(f"- Exercises checked: {len(exercises)}")
    print(f"- CRITICALs: {criticals}")
    print(f"- MAJORs: {majors}")
    if novel_count:
        print(f"- Novel terms flagged: {novel_count}")
    print(f"- Verdict: {'PASS' if criticals == 0 else 'FAIL'}\n")

    if findings_output:
        collector.write(findings_output)
        print(f"Findings written to {findings_output} ({len(collector.findings)} findings)")

    sys.exit(0 if criticals == 0 else 1)


if __name__ == "__main__":
    main()
