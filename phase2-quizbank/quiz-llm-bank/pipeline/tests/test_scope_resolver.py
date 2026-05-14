#!/usr/bin/env python3
"""Unit tests for pipeline/scope_resolver.py.

All fixtures use synthetic config — no real course data.
Run: python3 -m pytest pipeline/tests/test_scope_resolver.py -v
"""

import sys
from pathlib import Path

# Ensure pipeline/ is on the path so bare imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from scope_resolver import (
    build_term_pattern,
    extract_exercise_text,
    get_allowed_terms,
    get_excluded_terms,
    get_grouped_scope_terms,
    get_prerequisite_closure,
    get_session_order,
    parse_prerequisite_session_id,
)


# ── Fixtures ────────────────────────────────────────────────────────────────

def _make_cfg(sessions, foundational_terms=None):
    """Minimal config dict."""
    cfg = {"sessions": sessions, "languages": ["en", "fr"]}
    if foundational_terms is not None:
        cfg["foundational_terms"] = foundational_terms
    return cfg


def _session(sid, prereqs=None, scope_en=None, scope_fr=None, topics=None):
    return {
        "id": sid,
        "dir": sid,
        "title_en": sid,
        "title_fr": sid,
        "topics": topics or [],
        "prerequisites": prereqs or [],
        "exercise_count": 10,
        "type_distribution": {"MATH": 10},
        "scope_terms": {
            "en": scope_en or [],
            "fr": scope_fr or [],
        },
    }


# ── TestBuildTermPattern ────────────────────────────────────────────────────

class TestBuildTermPattern:
    def test_single_word(self):
        pat = build_term_pattern("OLS")
        assert pat is not None
        assert pat.search(" OLS ")

    def test_multi_word(self):
        pat = build_term_pattern("ordinary least squares")
        assert pat is not None
        assert pat.search(" ordinary least squares ")

    def test_hyphenated(self):
        pat = build_term_pattern("Breusch-Pagan test")
        assert pat is not None
        assert pat.search(" Breusch-Pagan test ")
        # Also matches with space instead of hyphen
        assert pat.search(" Breusch Pagan test ")

    def test_spaces_and_hyphens(self):
        pat = build_term_pattern("Cochrane-Orcutt")
        assert pat is not None
        assert pat.search(" Cochrane-Orcutt ")
        assert pat.search(" Cochrane Orcutt ")

    def test_parentheses(self):
        pat = build_term_pattern("AR(1)")
        assert pat is not None
        assert pat.search(" AR(1) ")

    def test_dots(self):
        pat = build_term_pattern("SLR.1")
        assert pat is not None
        assert pat.search(" SLR.1 ")

    def test_accented_chars(self):
        pat = build_term_pattern("régression linéaire")
        assert pat is not None
        assert pat.search(" régression linéaire ")

    def test_self_match_invariant(self):
        terms = [
            "OLS", "Breusch-Pagan test", "AR(1)", "SLR.1",
            "régression linéaire", "Gauss-Markov theorem",
        ]
        for t in terms:
            pat = build_term_pattern(t)
            assert pat is not None, f"Pattern is None for '{t}'"
            assert pat.search(f" {t} "), f"Self-match failed for '{t}'"

    def test_word_boundary_no_partial(self):
        pat = build_term_pattern("OLS")
        assert pat is not None
        # Should not match in the middle of a word
        assert not pat.search("POLS")
        assert not pat.search("BOLSA")

    def test_case_insensitive(self):
        pat = build_term_pattern("Blue")
        assert pat is not None
        assert pat.search(" blue ")
        assert pat.search(" BLUE ")

    def test_empty_returns_none(self):
        assert build_term_pattern("") is None
        assert build_term_pattern("   ") is None

    def test_none_input(self):
        # Defensive: although type hint says str, callers may pass None via dicts
        assert build_term_pattern(None) is None  # type: ignore[arg-type]


# ── TestGetPrerequisiteClosure ──────────────────────────────────────────────

class TestGetPrerequisiteClosure:
    def test_linear_chain(self):
        """S1 -> S2 -> S3: closure of S3 = {S1, S2}."""
        cfg = _make_cfg([
            _session("S1"),
            _session("S2", prereqs=["S1_intro"]),
            _session("S3", prereqs=["S2_prop"]),
        ])
        assert get_prerequisite_closure(cfg, "S3") == {"S1", "S2"}

    def test_diamond_dag(self):
        """S1 -> S2, S1 -> S3, S2+S3 -> S4."""
        cfg = _make_cfg([
            _session("S1"),
            _session("S2", prereqs=["S1_a"]),
            _session("S3", prereqs=["S1_b"]),
            _session("S4", prereqs=["S2_x", "S3_y"]),
        ])
        assert get_prerequisite_closure(cfg, "S4") == {"S1", "S2", "S3"}

    def test_no_prereqs(self):
        cfg = _make_cfg([_session("S1")])
        assert get_prerequisite_closure(cfg, "S1") == set()

    def test_cycle_no_infinite_loop(self):
        """S1 prereq S2, S2 prereq S1 — should terminate."""
        cfg = _make_cfg([
            _session("S1", prereqs=["S2_x"]),
            _session("S2", prereqs=["S1_y"]),
        ])
        closure = get_prerequisite_closure(cfg, "S1")
        assert "S2" in closure  # found S2
        # didn't hang

    def test_nonexistent_prereq_session(self):
        """Prerequisite references unknown session ID — silently ignored."""
        cfg = _make_cfg([
            _session("S1"),
            _session("S2", prereqs=["S99_missing"]),
        ])
        assert get_prerequisite_closure(cfg, "S2") == set()

    def test_nonexistent_session_id(self):
        cfg = _make_cfg([_session("S1")])
        assert get_prerequisite_closure(cfg, "S99") == set()


# ── TestGetAllowedTerms ────────────────────────────────────────────────────

class TestGetAllowedTerms:
    def test_own_terms(self):
        cfg = _make_cfg([_session("S1", scope_en=["OLS", "SLR"])])
        assert get_allowed_terms(cfg, "S1", "en") == ["OLS", "SLR"]

    def test_inherited_via_prereq(self):
        cfg = _make_cfg([
            _session("S1", scope_en=["OLS"]),
            _session("S2", prereqs=["S1_x"], scope_en=["BLUE"]),
        ])
        allowed = get_allowed_terms(cfg, "S2", "en")
        assert "OLS" in allowed
        assert "BLUE" in allowed

    def test_transitive_inheritance(self):
        cfg = _make_cfg([
            _session("S1", scope_en=["OLS"]),
            _session("S2", prereqs=["S1_x"], scope_en=["BLUE"]),
            _session("S3", prereqs=["S2_y"], scope_en=["WLS"]),
        ])
        allowed = get_allowed_terms(cfg, "S3", "en")
        assert "OLS" in allowed
        assert "BLUE" in allowed
        assert "WLS" in allowed

    def test_no_duplicates(self):
        cfg = _make_cfg([
            _session("S1", scope_en=["OLS", "R²"]),
            _session("S2", prereqs=["S1_x"], scope_en=["OLS", "BLUE"]),
        ])
        allowed = get_allowed_terms(cfg, "S2", "en")
        assert allowed.count("OLS") == 1

    def test_foundational_terms_after_introduction(self):
        cfg = _make_cfg(
            [
                _session("S1", scope_en=["OLS"]),
                _session("S2", prereqs=["S1_x"], scope_en=["BLUE"]),
                _session("S3", prereqs=["S2_y"], scope_en=["WLS"]),
            ],
            foundational_terms={
                "en": [{"term": "confidence interval", "introduced_in": "S2"}],
            },
        )
        # S1 is before S2 — should NOT have the foundational term
        assert "confidence interval" not in get_allowed_terms(cfg, "S1", "en")
        # S2 is where it's introduced — SHOULD have it
        assert "confidence interval" in get_allowed_terms(cfg, "S2", "en")
        # S3 is after S2 — SHOULD have it
        assert "confidence interval" in get_allowed_terms(cfg, "S3", "en")

    def test_foundational_terms_missing_key(self):
        """Backwards compat: no foundational_terms key in config."""
        cfg = _make_cfg([_session("S1", scope_en=["OLS"])])
        # Should not crash
        assert get_allowed_terms(cfg, "S1", "en") == ["OLS"]

    def test_unknown_session(self):
        cfg = _make_cfg([_session("S1", scope_en=["OLS"])])
        assert get_allowed_terms(cfg, "S99", "en") == []


# ── TestGetExcludedTerms ───────────────────────────────────────────────────

class TestGetExcludedTerms:
    def test_later_terms_excluded(self):
        cfg = _make_cfg([
            _session("S1", scope_en=["OLS"]),
            _session("S2", prereqs=["S1_x"], scope_en=["BLUE"]),
            _session("S3", prereqs=["S2_y"], scope_en=["WLS"]),
        ])
        excluded = get_excluded_terms(cfg, "S1", "en")
        assert "BLUE" in excluded
        assert "WLS" in excluded
        assert "OLS" not in excluded

    def test_allowed_terms_not_excluded(self):
        cfg = _make_cfg([
            _session("S1", scope_en=["OLS"]),
            _session("S2", prereqs=["S1_x"], scope_en=["OLS", "BLUE"]),
        ])
        # OLS is in both S1 and S2; from S1's perspective, S2's "OLS" is allowed
        excluded = get_excluded_terms(cfg, "S1", "en")
        assert "OLS" not in excluded
        assert "BLUE" in excluded

    def test_last_session_empty_excluded(self):
        cfg = _make_cfg([
            _session("S1", scope_en=["OLS"]),
            _session("S2", prereqs=["S1_x"], scope_en=["BLUE"]),
        ])
        assert get_excluded_terms(cfg, "S2", "en") == []

    def test_no_scope_terms_returns_empty(self):
        cfg = _make_cfg([_session("S1")])
        assert get_excluded_terms(cfg, "S1", "en") == []


# ── TestExtractExerciseText ─────────────────────────────────────────────────

class TestExtractExerciseText:
    def test_all_fields_present(self):
        ex = {
            "question_text": "What is OLS?",
            "data_table": "| X | Y |",
            "solution": {
                "text": "OLS minimises SSR.",
                "key_formula": "beta = (X'X)^-1 X'Y",
                "common_mistakes": ["Confusing SSE with SSR"],
            },
            "hints": ["Think about minimisation", "Use calculus"],
        }
        text = extract_exercise_text(ex)
        assert "What is OLS?" in text
        assert "| X | Y |" in text
        assert "OLS minimises SSR." in text
        assert "beta = (X'X)^-1 X'Y" in text
        assert "Confusing SSE with SSR" in text
        assert "Think about minimisation" in text

    def test_missing_fields(self):
        ex = {"question_text": "Simple question"}
        text = extract_exercise_text(ex)
        assert "Simple question" in text

    def test_solution_as_string(self):
        ex = {"question_text": "Q", "solution": "Just a string answer"}
        text = extract_exercise_text(ex)
        assert "Just a string answer" in text

    def test_empty_exercise(self):
        text = extract_exercise_text({})
        # Should not crash — returns empty-ish string
        assert isinstance(text, str)

    def test_non_string_fields_no_crash(self):
        """Non-string question_text, hints, etc. should not raise TypeError."""
        ex = {
            "question_text": {"nested": "dict"},
            "hints": [1, None, "ok"],
            "solution": {"text": 42, "key_formula": None},
        }
        text = extract_exercise_text(ex)
        assert isinstance(text, str)
        assert "ok" in text


# ── TestParsePrerequisiteSessionId ──────────────────────────────────────────

class TestParsePrerequisiteSessionId:
    def test_exact_match(self):
        assert parse_prerequisite_session_id("S1", {"S1", "S2"}) == "S1"

    def test_prefix_with_topic(self):
        assert parse_prerequisite_session_id("S1_SLR_model", {"S1", "S2"}) == "S1"

    def test_no_match(self):
        assert parse_prerequisite_session_id("S99_missing", {"S1", "S2"}) is None

    def test_empty_known(self):
        assert parse_prerequisite_session_id("S1", set()) is None

    def test_overlapping_ids_longest_match(self):
        """When IDs overlap (S1 vs S1_ADV), the longest match wins."""
        assert parse_prerequisite_session_id("S1_ADV_topic", {"S1", "S1_ADV"}) == "S1_ADV"

    def test_overlapping_ids_deterministic(self):
        """Result must be stable across multiple calls (no set iteration order issues)."""
        known = {"S1", "S1_ADV"}
        results = {parse_prerequisite_session_id("S1_ADV_topic", known) for _ in range(20)}
        assert results == {"S1_ADV"}


# ── TestGetSessionOrder ─────────────────────────────────────────────────────

class TestGetSessionOrder:
    def test_basic(self):
        cfg = _make_cfg([_session("S1"), _session("S2"), _session("S3")])
        order = get_session_order(cfg)
        assert order == {"S1": 0, "S2": 1, "S3": 2}


# ── TestGetGroupedScopeTerms ────────────────────────────────────────────────

class TestGetGroupedScopeTerms:
    """The grouped helper underpins prompt-side scope guards and audit
    target_session suggestions, so it must keep the three groups disjoint
    and ordered deterministically."""

    def test_three_groups_disjoint(self):
        cfg = _make_cfg([
            _session("S1", scope_en=["t-test"]),
            _session("S2", prereqs=["S1"], scope_en=["heteroskedasticity"]),
            _session("S3", prereqs=["S2"], scope_en=["instrumental variables"]),
        ])
        g = get_grouped_scope_terms(cfg, "S2", "en")
        own = {t for t, _ in g["this_session"]}
        prereq = {t for t, _ in g["prereq"]}
        forbidden = {t for t, _ in g["forbidden"]}

        assert own == {"heteroskedasticity"}
        assert prereq == {"t-test"}
        assert forbidden == {"instrumental variables"}
        # Disjoint sets — no term appears in more than one group
        assert own & prereq == set()
        assert own & forbidden == set()
        assert prereq & forbidden == set()

    def test_target_session_for_forbidden_terms(self):
        """The introduction session lets the auditor suggest a reclassify target."""
        cfg = _make_cfg([
            _session("S1"),
            _session("S2"),
            _session("S8", scope_en=["instrumental variables"]),
        ])
        g = get_grouped_scope_terms(cfg, "S1", "en")
        forbidden = dict(g["forbidden"])
        # The auditor reading this can suggest target_session="S8" for an
        # S1 exercise about instrumental variables.
        assert forbidden["instrumental variables"] == "S8"

    def test_first_session_has_no_prereq_or_forbidden_when_alone(self):
        cfg = _make_cfg([_session("S1", scope_en=["OLS"])])
        g = get_grouped_scope_terms(cfg, "S1", "en")
        assert g["this_session"] == [("OLS", "S1")]
        assert g["prereq"] == []
        assert g["forbidden"] == []

    def test_foundational_terms_appear_in_prereq_when_introduced_earlier(self):
        cfg = _make_cfg(
            [_session("S1"), _session("S2"), _session("S3")],
            foundational_terms={
                "en": [{"term": "p-value", "introduced_in": "S1"}],
            },
        )
        g = get_grouped_scope_terms(cfg, "S2", "en")
        prereq = dict(g["prereq"])
        assert prereq.get("p-value") == "S1"

    def test_unknown_session_returns_empty_groups(self):
        cfg = _make_cfg([_session("S1")])
        g = get_grouped_scope_terms(cfg, "S99", "en")
        assert g == {"this_session": [], "prereq": [], "forbidden": []}

    def test_deterministic_ordering(self):
        """Repeated calls return the same ordering — no set iteration leakage."""
        cfg = _make_cfg([
            _session("S1", scope_en=["t-test", "OLS", "p-value"]),
            _session("S2", prereqs=["S1"], scope_en=["heteroskedasticity"]),
            _session("S3", prereqs=["S2"], scope_en=["IV", "DiD", "panel"]),
        ])
        results = [
            tuple((g["this_session"], g["prereq"], g["forbidden"]))
            for g in (get_grouped_scope_terms(cfg, "S2", "en") for _ in range(10))
        ]
        assert all(r == results[0] for r in results)

    def test_short_mixedcase_acronym_matches_case_sensitive(self):
        """Short mixed-case acronyms like DiD should NOT match the English
        word 'did' — that was a real false positive in the validator output.
        """
        p = build_term_pattern("DiD")
        assert p is not None
        # Must match the acronym
        assert p.search("DiD is widely used")
        # Must NOT match the lowercase English word
        assert not p.search("did not include")
        assert not p.search("she did the analysis")
        # Hyphenated form should still match
        p2 = build_term_pattern("DiD")
        assert p2.search("the DiD estimator")

    def test_long_or_uppercase_terms_remain_case_insensitive(self):
        """Longer terms and pure-uppercase acronyms keep the previous
        case-insensitive behavior."""
        p = build_term_pattern("Heteroskedasticity")
        assert p.search("heteroskedasticity is a problem")
        # Pure uppercase, not mixed case → stays case-insensitive
        p2 = build_term_pattern("OLS")
        assert p2.search("ols regression")
        # Multi-word with at least one long token → case-insensitive
        p3 = build_term_pattern("Breusch-Pagan test")
        assert p3.search("breusch-pagan test")

    def test_case_insensitive_dedup_across_groups(self):
        """If the same term appears in current and earlier sessions (case-insensitive),
        it should not appear in both this_session and prereq."""
        cfg = _make_cfg([
            _session("S1", scope_en=["OLS"]),
            _session("S2", prereqs=["S1"], scope_en=["ols"]),
        ])
        g = get_grouped_scope_terms(cfg, "S2", "en")
        own_terms = {t.lower() for t, _ in g["this_session"]}
        prereq_terms = {t.lower() for t, _ in g["prereq"]}
        # The current-session entry takes precedence; prereq stays empty for that term
        assert "ols" in own_terms
        assert "ols" not in prereq_terms
