#!/usr/bin/env python3
"""Load and validate course_config.json — single source of truth for all pipeline tools."""

import json
import re
import sys
from pathlib import Path

# Default config location: project root / course_config.json
_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "course_config.json"


def load_config(path: str | Path | None = None) -> dict:
    """Load course_config.json, validate required keys, return dict."""
    p = Path(path) if path else _DEFAULT_CONFIG
    if not p.exists():
        print(f"ERROR: config not found at {p}", file=sys.stderr)
        sys.exit(1)
    with open(p, encoding="utf-8") as f:
        cfg = json.load(f)
    _validate(cfg, str(p))
    return cfg


_REQUIRED_TOP = [
    "course_id", "languages", "sessions", "exercise_types",
    "difficulty_distribution", "id_regex", "solution_constraints",
    "math_validation", "pipeline",
]

_REQUIRED_SESSION = ["id", "dir", "topics", "exercise_count", "type_distribution"]
_KNOWN_LLM_PROVIDERS = {"claude", "codex", "openai", "ollama", "vibe"}


def _validate(cfg: dict, path: str):
    missing = [k for k in _REQUIRED_TOP if k not in cfg]
    if missing:
        print(f"ERROR: {path} missing keys: {missing}", file=sys.stderr)
        sys.exit(1)

    _validate_assessment_style_gate(cfg, path)

    langs = cfg["languages"]
    if not isinstance(langs, list) or len(langs) < 1:
        print(f"ERROR: {path} 'languages' must be a non-empty list", file=sys.stderr)
        sys.exit(1)

    for i, s in enumerate(cfg["sessions"]):
        sm = [k for k in _REQUIRED_SESSION if k not in s]
        if sm:
            print(f"ERROR: session[{i}] missing keys: {sm}", file=sys.stderr)
            sys.exit(1)
        # Validate that session has a title for each configured language
        for lang in langs:
            title_key = f"title_{lang}"
            if title_key not in s:
                print(f"ERROR: session[{i}] missing '{title_key}' (required by languages config)", file=sys.stderr)
                sys.exit(1)
        # Validate type_distribution sums to exercise_count
        td = s.get("type_distribution", {})
        td_sum = sum(td.values())
        if td_sum != s["exercise_count"]:
            print(f"WARNING: session[{i}] type_distribution sums to {td_sum}, expected {s['exercise_count']}", file=sys.stderr)

    # Validate difficulty_distribution sums to ~1.0
    dd = cfg["difficulty_distribution"]
    total = sum(dd.values())
    if abs(total - 1.0) > 0.05:
        print(f"WARNING: difficulty_distribution sums to {total}, expected ~1.0", file=sys.stderr)

    # Validate prerequisite references (non-fatal warnings)
    known_session_ids = {s["id"] for s in cfg["sessions"]}
    for i, s in enumerate(cfg["sessions"]):
        for prereq in s.get("prerequisites", []):
            matched = False
            for sid in known_session_ids:
                if prereq == sid or prereq.startswith(sid + "_"):
                    matched = True
                    break
            if not matched:
                print(
                    f"WARNING: session[{i}] ({s['id']}) prerequisite '{prereq}' "
                    f"does not match any known session ID",
                    file=sys.stderr,
                )

    # Validate prerequisite DAG has no cycles (import scope_resolver lazily
    # to avoid circular dependency — config_loader is imported first everywhere)
    try:
        from scope_resolver import get_prerequisite_closure
        for s in cfg["sessions"]:
            closure = get_prerequisite_closure(cfg, s["id"])
            if s["id"] in closure:
                print(
                    f"WARNING: session '{s['id']}' has a cycle in its prerequisite DAG",
                    file=sys.stderr,
                )
    except ImportError:
        pass  # scope_resolver not available (e.g. standalone config_loader usage)

    # Validate foundational_terms (if present)
    ft = cfg.get("foundational_terms", {})
    if ft and not isinstance(ft, dict):
        print(f"WARNING: foundational_terms should be an object (got {type(ft).__name__})", file=sys.stderr)
        ft = {}
    if ft:
        for lang, entries in ft.items():
            if not isinstance(entries, list):
                print(
                    f"WARNING: foundational_terms['{lang}'] should be a list",
                    file=sys.stderr,
                )
                continue
            for j, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    print(
                        f"WARNING: foundational_terms['{lang}'][{j}] should be an object",
                        file=sys.stderr,
                    )
                    continue
                if "term" not in entry:
                    print(
                        f"WARNING: foundational_terms['{lang}'][{j}] missing 'term' key",
                        file=sys.stderr,
                    )
                if "introduced_in" not in entry:
                    print(
                        f"WARNING: foundational_terms['{lang}'][{j}] missing 'introduced_in' key",
                        file=sys.stderr,
                    )
                elif entry["introduced_in"] not in known_session_ids:
                    print(
                        f"WARNING: foundational_terms['{lang}'][{j}] "
                        f"'introduced_in' = '{entry['introduced_in']}' is not a valid session ID",
                        file=sys.stderr,
                    )

    # Validate topic_aliases type (if present)
    ta = cfg.get("topic_aliases")
    if ta is not None and not isinstance(ta, dict):
        print(f"WARNING: topic_aliases should be an object (got {type(ta).__name__})", file=sys.stderr)

    # Validate content_boundary type (if present)
    cb = cfg.get("content_boundary")
    if cb is not None and not isinstance(cb, dict):
        print(f"WARNING: content_boundary should be an object (got {type(cb).__name__})", file=sys.stderr)

    if "llm" in cfg:
        _validate_llm_section(cfg["llm"], path)
    else:
        scaling = cfg.get("scaling", {})
        if not isinstance(scaling, dict):
            scaling = {}
        claude_model = scaling.get("claude_model", "claude-opus-4-7")
        codex_model = scaling.get("codex_model", "gpt-5.4")
        print(
            "WARNING: config is missing top-level 'llm'; "
            "falling back to deprecated scaling.claude_model/scaling.codex_model fields",
            file=sys.stderr,
        )
        cfg["llm"] = {
            "generation": {
                "provider": "claude",
                "model": claude_model,
            },
            "verifiers": [
                {
                    "provider": "codex",
                    "model": codex_model,
                }
            ],
        }


def _validate_assessment_style_gate(cfg: dict, path: str) -> None:
    """Refuse to run generation from an unresolved assessment-style profile."""
    exercise_profile = cfg.get("exercise_profile")
    profile_basis = (
        exercise_profile.get("basis")
        if isinstance(exercise_profile, dict)
        else None
    )
    basis = cfg.get("assessment_style_basis") or profile_basis
    if basis == "pending_assessment_style_audit":
        print(
            "ERROR: "
            f"{path} still has an assessment-style basis of 'pending_assessment_style_audit'. "
            "Inspect real assessment/practice material, write ASSESSMENT_STYLE_AUDIT.md, "
            "then set assessment_style_basis and assessment_style_evidence before generation.",
            file=sys.stderr,
        )
        sys.exit(1)


def _validate_llm_section(llm_cfg: dict, path: str) -> None:
    if not isinstance(llm_cfg, dict):
        print(f"ERROR: {path} 'llm' must be an object", file=sys.stderr)
        sys.exit(1)

    generation = llm_cfg.get("generation")
    if not isinstance(generation, dict):
        print(f"ERROR: {path} 'llm.generation' must be an object", file=sys.stderr)
        sys.exit(1)
    _validate_llm_provider_config(generation, "llm.generation", path)

    verifiers = llm_cfg.get("verifiers")
    if not isinstance(verifiers, list):
        print(f"ERROR: {path} 'llm.verifiers' must be a list", file=sys.stderr)
        sys.exit(1)
    for i, verifier in enumerate(verifiers):
        if not isinstance(verifier, dict):
            print(
                f"ERROR: {path} 'llm.verifiers[{i}]' must be an object",
                file=sys.stderr,
            )
            sys.exit(1)
        _validate_llm_provider_config(verifier, f"llm.verifiers[{i}]", path)


def _validate_llm_provider_config(provider_cfg: dict, field_name: str, path: str) -> None:
    provider = provider_cfg.get("provider")
    if not isinstance(provider, str) or not provider.strip():
        print(
            f"ERROR: {path} '{field_name}.provider' must be a non-empty string",
            file=sys.stderr,
        )
        sys.exit(1)
    if provider not in _KNOWN_LLM_PROVIDERS:
        print(
            f"WARNING: {path} '{field_name}.provider' = {provider!r} is not a known provider; "
            "validation will continue and the call site will raise a clearer error if invoked",
            file=sys.stderr,
        )


def get_output_dir(cfg: dict) -> Path:
    """Return output/<course_id>/ path relative to project root."""
    root = Path(__file__).resolve().parent.parent
    return root / "output" / cfg["course_id"]


def get_session_dirs(cfg: dict) -> dict[str, str]:
    """Return {session_id: dir_name} mapping, e.g. {'ch1': 'ch1_Introduction'}."""
    return {s["id"]: s["dir"] for s in cfg["sessions"]}


def get_session_path(cfg: dict, session_id: str) -> Path:
    """Return full path to a session output directory."""
    out = get_output_dir(cfg)
    dirs = get_session_dirs(cfg)
    if session_id not in dirs:
        raise KeyError(f"Unknown session: {session_id}")
    return out / dirs[session_id]


def get_validation_dir(cfg: dict) -> Path:
    """Return output/<course_id>/validation/ path."""
    return get_output_dir(cfg) / "validation"


def get_languages(cfg: dict) -> list[str]:
    """Return configured language codes, e.g. ['en', 'fr']."""
    return cfg["languages"]


def get_primary_language(cfg: dict) -> str:
    """Return the first configured language (used for counting to avoid double-counting)."""
    return cfg["languages"][0]


def get_json_files(cfg: dict) -> list[str]:
    """Return list of JSON filenames to expect per session (e.g. exercises_EN.json)."""
    files = []
    for lang in cfg["languages"]:
        files.append(f"exercises_{lang.upper()}.json")
    if cfg.get("software_tool"):
        tool = cfg["software_tool"].lower()
        for lang in cfg["languages"]:
            files.append(f"{tool}_{lang.upper()}.json")
    return files


def get_id_pattern(cfg: dict) -> re.Pattern:
    """Return compiled regex for exercise ID validation."""
    return re.compile(cfg["id_regex"])


def get_tolerance(cfg: dict) -> tuple[float, float]:
    """Return (relative_tolerance, absolute_tolerance) for math validation."""
    mv = cfg["math_validation"]
    return mv.get("tolerance_relative", 0.02), mv.get("tolerance_absolute", 0.05)


# ── Scaling config ──

_SCALING_DEFAULTS = {
    "claude_model": "claude-opus-4-7",
    "codex_model": "gpt-5.4",
    "max_parallel_batches": 4,
    "max_retries_per_batch": 3,
    "subprocess_timeout_secs": 300,
    "large_slide_max_chars": 200_000,
}


def get_scaling_config(cfg: dict) -> dict:
    """Return scaling config with defaults for any missing keys."""
    user = cfg.get("scaling", {})
    return {**_SCALING_DEFAULTS, **user}


def get_inbox_files(cfg: dict, session_id: str) -> list[str]:
    """Resolve inbox file content for a session.

    Checks session-level inbox_files first, then falls back to
    inbox/Slides/{session_id}/ or inbox/Slides/{session_dir}/.
    Returns list of file paths (as strings).
    """
    import glob as globmod

    root = Path(__file__).resolve().parent.parent
    session = next((s for s in cfg["sessions"] if s["id"] == session_id), None)
    if not session:
        return []

    patterns = session.get("inbox_files", [])
    if not patterns:
        inbox_dir = root / "inbox" / "Slides"
        for candidate in [session_id, session["dir"]]:
            d = inbox_dir / candidate
            if d.is_dir():
                patterns = [str(d / "*.md")]
                break

    results = []
    for pat in patterns:
        if not Path(pat).is_absolute():
            pat = str(root / pat)
        results.extend(sorted(globmod.glob(pat)))
    return results


if __name__ == "__main__":
    # Quick smoke test: load and print summary
    cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"Course: {cfg['course_id']}")
    print(f"Sessions: {len(cfg['sessions'])}")
    print(f"Output dir: {get_output_dir(cfg)}")
    print(f"Session dirs: {get_session_dirs(cfg)}")
    print(f"JSON files: {get_json_files(cfg)}")
