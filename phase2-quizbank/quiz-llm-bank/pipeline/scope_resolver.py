#!/usr/bin/env python3
"""Shared scope-resolution logic — single source of truth.

Extracted from prompt_renderer.py and validate_content_boundary.py to
eliminate duplication.  This module deliberately does NOT import
config_loader (no circular dependency risk).

Public API
----------
get_session_order(cfg) -> dict[str, int]
get_prerequisite_closure(cfg, session_id) -> set[str]
parse_prerequisite_session_id(prereq_str, known_ids) -> str | None
get_allowed_terms(cfg, session_id, language) -> list[str]
get_excluded_terms(cfg, session_id, language) -> list[str]
build_term_pattern(term) -> re.Pattern | None
extract_exercise_text(exercise) -> str
"""

import re


# ---------------------------------------------------------------------------
# Session ordering
# ---------------------------------------------------------------------------

def get_session_order(cfg: dict) -> dict[str, int]:
    """Return {session_id: positional_index} for every session."""
    return {s["id"]: i for i, s in enumerate(cfg["sessions"])}


# ---------------------------------------------------------------------------
# Prerequisite helpers
# ---------------------------------------------------------------------------

def parse_prerequisite_session_id(prereq_str: str, known_ids: set[str]) -> str | None:
    """Extract a session ID from a prerequisite string like 'S1_SLR_model'.

    When IDs overlap (e.g. 'S1' and 'S1_ADV'), the longest matching ID wins.
    Returns the matching session ID or None if no known ID matches.
    """
    best: str | None = None
    for sid in known_ids:
        if prereq_str == sid or prereq_str.startswith(sid + "_"):
            if best is None or len(sid) > len(best):
                best = sid
    return best


def get_prerequisite_closure(cfg: dict, session_id: str) -> set[str]:
    """Return the *transitive* set of prerequisite session IDs for *session_id*.

    Cycle-safe: visited nodes are never re-enqueued.
    """
    session_by_id = {s["id"]: s for s in cfg["sessions"]}
    known_ids = set(session_by_id)

    session = session_by_id.get(session_id)
    if session is None:
        return set()

    visited: set[str] = set()
    queue: list[str] = []

    for p in session.get("prerequisites", []):
        psid = parse_prerequisite_session_id(p, known_ids)
        if psid is not None and psid not in visited:
            queue.append(psid)

    while queue:
        psid = queue.pop()
        if psid in visited:
            continue
        visited.add(psid)
        ps = session_by_id.get(psid)
        if ps:
            for p2 in ps.get("prerequisites", []):
                child = parse_prerequisite_session_id(p2, known_ids)
                if child is not None and child not in visited:
                    queue.append(child)

    return visited


# ---------------------------------------------------------------------------
# Scope-term collection
# ---------------------------------------------------------------------------

def get_allowed_terms(cfg: dict, session_id: str, language: str) -> list[str]:
    """Return the flat, deduplicated list of allowed scope terms.

    Includes:
      - own session scope_terms
      - all transitive prerequisite scope_terms
      - foundational_terms whose ``introduced_in`` session is <= current
    """
    session_by_id = {s["id"]: s for s in cfg["sessions"]}
    session_order = get_session_order(cfg)
    prereq_sids = get_prerequisite_closure(cfg, session_id)

    session = session_by_id.get(session_id)
    if session is None:
        return []

    # Own terms first
    all_terms: list[str] = list(
        session.get("scope_terms", {}).get(language, [])
    )

    # Prerequisite terms (ordered by session index for determinism)
    for psid in sorted(prereq_sids, key=lambda s: session_order.get(s, 0)):
        ps = session_by_id.get(psid)
        if ps:
            for t in ps.get("scope_terms", {}).get(language, []):
                if t not in all_terms:
                    all_terms.append(t)

    # Foundational terms (backwards-compatible: key may be absent)
    current_idx = session_order.get(session_id, 0)
    for ft in cfg.get("foundational_terms", {}).get(language, []):
        term = ft.get("term", "")
        intro = ft.get("introduced_in", "")
        if not term:
            continue
        if session_order.get(intro, float("inf")) <= current_idx:
            if term not in all_terms:
                all_terms.append(term)

    return all_terms


def get_excluded_terms(cfg: dict, session_id: str, language: str) -> list[str]:
    """Return scope terms from later sessions that are NOT in the allowed set.

    If no session has scope_terms at all, returns [].
    """
    if not any(s.get("scope_terms") for s in cfg["sessions"]):
        return []

    session_order = get_session_order(cfg)
    current_idx = session_order.get(session_id)
    if current_idx is None:
        return []

    allowed_lower = {t.lower() for t in get_allowed_terms(cfg, session_id, language)}

    excluded: list[str] = []
    for s in cfg["sessions"]:
        if session_order[s["id"]] <= current_idx:
            continue
        for t in s.get("scope_terms", {}).get(language, []):
            if t.lower() not in allowed_lower and t not in excluded:
                excluded.append(t)

    return excluded


# ---------------------------------------------------------------------------
# Grouped scope terms (for prompt injection + audit context)
# ---------------------------------------------------------------------------

def get_grouped_scope_terms(
    cfg: dict, session_id: str, language: str,
) -> dict[str, list[tuple[str, str]]]:
    """Return scope terms grouped by status with their introduction session.

    Groups:
      "this_session" — terms whose `scope_terms` list is on the current session
      "prereq"       — terms inherited from prerequisite sessions or
                       foundational_terms introduced at or before the current
                       session
      "forbidden"    — terms from later sessions (the model must NOT use them)

    Each entry is a `(term, introduction_session_id)` tuple.  Order is
    deterministic: own-session first, then prereq sessions in session-order,
    then forbidden sessions in session-order.

    Used by the generation prompt (to give the LLM an explicit allow/deny
    list) and by the audit prompts (to suggest a `target_session` when
    flagging forward references).
    """
    session_by_id = {s["id"]: s for s in cfg["sessions"]}
    session_order = get_session_order(cfg)

    if session_id not in session_by_id:
        return {"this_session": [], "prereq": [], "forbidden": []}

    current_idx = session_order[session_id]
    prereq_sids = get_prerequisite_closure(cfg, session_id)

    this_session: list[tuple[str, str]] = []
    prereq: list[tuple[str, str]] = []
    forbidden: list[tuple[str, str]] = []

    seen_terms: set[str] = set()

    # Own session terms
    own = session_by_id[session_id].get("scope_terms", {}).get(language, [])
    for t in own:
        if t.lower() not in seen_terms:
            seen_terms.add(t.lower())
            this_session.append((t, session_id))

    # Prerequisite session terms (ordered by session index)
    for psid in sorted(prereq_sids, key=lambda s: session_order.get(s, 0)):
        ps = session_by_id.get(psid)
        if not ps:
            continue
        for t in ps.get("scope_terms", {}).get(language, []):
            if t.lower() not in seen_terms:
                seen_terms.add(t.lower())
                prereq.append((t, psid))

    # Foundational terms introduced at or before the current session
    for ft in cfg.get("foundational_terms", {}).get(language, []):
        term = ft.get("term", "")
        intro = ft.get("introduced_in", "")
        if not term or term.lower() in seen_terms:
            continue
        intro_idx = session_order.get(intro, float("inf"))
        if intro_idx <= current_idx:
            seen_terms.add(term.lower())
            prereq.append((term, intro or session_id))

    # Forbidden: later-session scope_terms not already in allowed
    for s in cfg["sessions"]:
        sid = s["id"]
        if session_order[sid] <= current_idx:
            continue
        for t in s.get("scope_terms", {}).get(language, []):
            if t.lower() in seen_terms:
                continue
            if any(t.lower() == ft.lower() for ft, _ in forbidden):
                continue
            forbidden.append((t, sid))

    return {
        "this_session": this_session,
        "prereq": prereq,
        "forbidden": forbidden,
    }


# ---------------------------------------------------------------------------
# Term pattern
# ---------------------------------------------------------------------------

def build_term_pattern(term: str) -> re.Pattern | None:
    """Build a whole-word regex for *term*.

    Tokenises by whitespace/hyphens, escapes each part, joins with a
    flexible ``[\\s\\-]+`` separator. Returns None for empty/blank terms.

    Case sensitivity:
    - **Short acronyms with mixed case** (any token ≤4 chars with both
      uppercase and lowercase, e.g. ``DiD``, ``MCG``, ``RLS``) match
      case-sensitively. This prevents false positives like the English
      word ``did`` matching the difference-in-differences acronym.
    - All other terms (e.g. ``Heteroskedasticity``, ``OLS``,
      ``Breusch-Pagan test``) match case-insensitively, since they would
      not collide with common words.
    """
    if not term or not term.strip():
        return None
    parts = re.split(r"[\s\-]+", term.strip())
    parts = [p for p in parts if p]
    if not parts:
        return None
    body = r"[\s\-]+".join(re.escape(p) for p in parts)

    # Acronym signature: short token (≤4 chars) with uppercase letters
    # appearing AFTER the first character (e.g. "DiD", "MwG"). A simple
    # capitalized word like "Blue" or "Stata" only has uppercase at index 0
    # and is treated as a regular word — case-insensitive.
    def _is_short_acronym(p: str) -> bool:
        if len(p) > 4 or len(p) < 2:
            return False
        return any(c.isupper() for c in p[1:]) and any(c.islower() for c in p)

    flags = 0 if any(_is_short_acronym(p) for p in parts) else re.IGNORECASE

    return re.compile(
        r"(?<![A-Za-zÀ-ÿ0-9])" + body + r"(?![A-Za-zÀ-ÿ0-9])",
        flags,
    )


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def _str(val) -> str:
    """Coerce a value to str, returning '' for non-string types."""
    return val if isinstance(val, str) else ""


def extract_exercise_text(exercise: dict) -> str:
    """Concatenate all text fields relevant for scope checking.

    Robust to malformed payloads: non-string values are silently skipped.
    """
    parts: list[str] = []
    parts.append(_str(exercise.get("question_text", "")))

    dt = exercise.get("data_table")
    if isinstance(dt, str):
        parts.append(dt)

    sol = exercise.get("solution") or {}
    if isinstance(sol, dict):
        parts.append(_str(sol.get("text", "")))
        parts.append(_str(sol.get("key_formula", "")))
        for cm in sol.get("common_mistakes", []) or []:
            if isinstance(cm, str):
                parts.append(cm)
    elif isinstance(sol, str):
        parts.append(sol)

    for hint in exercise.get("hints", []) or []:
        if isinstance(hint, str):
            parts.append(hint)

    return "\n".join(parts)
