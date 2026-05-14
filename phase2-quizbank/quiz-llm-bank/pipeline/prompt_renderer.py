#!/usr/bin/env python3
"""Render prompt templates for batched generation, twin, audit, and fix calls.

Loads templates from prompts/, substitutes {{variables}} and {{#if}} blocks,
inlines inbox content (since --tools "" disables file reading), and builds
per-batch JSON schemas for --json-schema enforcement.
"""

import glob as globmod
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from scope_resolver import get_allowed_terms, get_excluded_terms

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

def _read_template(name: str) -> str:
    """Read a prompt template file from prompts/."""
    path = _PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")


def _resolve_conditionals(text: str, variables: dict) -> str:
    """Process {{#if var}}...{{/if}} blocks."""
    pattern = r"\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}"
    def replacer(m):
        var_name = m.group(1)
        content = m.group(2)
        if variables.get(var_name):
            return content
        return ""
    return re.sub(pattern, replacer, text, flags=re.DOTALL)


def _substitute(text: str, variables: dict) -> str:
    """Replace {{variable}} placeholders."""
    def replacer(m):
        key = m.group(1)
        val = variables.get(key, m.group(0))
        if isinstance(val, (list, dict)):
            return json.dumps(val, ensure_ascii=False)
        return str(val)
    return re.sub(r"\{\{(\w+)\}\}", replacer, text)


def _build_difficulty_calibration(cfg: dict) -> str:
    levels = list(cfg["difficulty_distribution"].keys())
    lines = []
    for i, level in enumerate(levels):
        if i == 0:
            lines.append(f"- {level}: lowest difficulty — 1-2 steps, single concept")
        elif i == len(levels) - 1:
            lines.append(f"- {level}: highest difficulty — multi-step synthesis across topics")
        else:
            lines.append(f"- {level}: moderate — 2-3 concepts combined")
    return "\n".join(lines)


def _build_type_distribution_text(type_dist: dict) -> str:
    """Format type distribution for prompt."""
    lines = []
    for typ, count in type_dist.items():
        lines.append(f"- {typ}: {count} exercises")
    return "\n".join(lines)


def _build_difficulty_distribution_text(cfg: dict) -> str:
    lines = []
    for level, pct in cfg["difficulty_distribution"].items():
        lines.append(f"- {level}: ~{int(pct * 100)}%")
    return "\n".join(lines)


def _build_assessment_style_text(cfg: dict) -> str:
    """Format optional audit evidence that justifies the exercise profile."""
    evidence = cfg.get("assessment_style_evidence") or []
    basis = cfg.get("assessment_style_basis") or cfg.get("assessment_style_audit")
    lines = []
    if basis:
        lines.append(f"- Basis: {basis}")
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict):
                path = item.get("path") or item.get("source") or "unspecified source"
                observed = item.get("observed") or item.get("note") or item.get("style") or ""
                lines.append(f"- {path}: {observed}".rstrip())
            else:
                lines.append(f"- {item}")
    elif isinstance(evidence, str):
        lines.append(evidence)
    return "\n".join(lines)


def _build_quiz_mode_constraints_text(cfg: dict) -> str:
    constraints = (
        cfg.get("quiz_mode_constraints")
        or cfg.get("ta_quiz_constraints")
    )
    if not constraints:
        return ""
    if isinstance(constraints, str):
        return constraints
    if isinstance(constraints, list):
        return "\n".join(f"- {item}" for item in constraints)
    if isinstance(constraints, dict):
        lines = []
        for key, value in constraints.items():
            if isinstance(value, list):
                rendered = ", ".join(str(v) for v in value)
            else:
                rendered = str(value)
            lines.append(f"- {key}: {rendered}")
        return "\n".join(lines)
    return str(constraints)


def _build_session_title_fields(cfg: dict, session: dict) -> str:
    """Build JSON snippet for session_title fields."""
    lines = []
    for lang in cfg["languages"]:
        title = session.get(f"title_{lang}", "")
        escaped = json.dumps(title, ensure_ascii=False)  # proper JSON escaping
        lines.append(f'  "session_title_{lang}": {escaped},')
    return "\n".join(lines)


def _build_glossary_text(cfg: dict, target_lang: str) -> str:
    """Build glossary table for target language."""
    terms = cfg.get("glossary_terms", [])
    if not terms:
        return "(no glossary configured)"
    source_lang = cfg["languages"][0]
    lines = [f"| {source_lang.upper()} | {target_lang.upper()} | Note |",
             "|---|---|---|"]
    for t in terms:
        src = t.get(source_lang, "")
        tgt = t.get(target_lang, "")
        note = t.get("note", "")
        lines.append(f"| {src} | {tgt} | {note} |")
    return "\n".join(lines)


def _build_scope_terms_text(cfg: dict, session: dict, language: str) -> str:
    """Build a bullet list of allowed scope_terms for this session."""
    all_terms = get_allowed_terms(cfg, session["id"], language)
    if not all_terms:
        return ""
    return "\n".join(f"- {t}" for t in all_terms)


def _build_excluded_terms_text(cfg: dict, session: dict, language: str) -> str:
    """Build a comma-separated list of terms from later sessions that must NOT
    appear in this session's exercises.
    """
    excluded = get_excluded_terms(cfg, session["id"], language)
    if not excluded:
        return ""
    return ", ".join(excluded)


def _build_scope_terms_grouped_text(cfg: dict, session: dict, language: str) -> str:
    """Render allowed/prereq/forbidden scope terms grouped by status, with
    each term tagged by its introduction session ID.

    The auditor and the generator both rely on this rendering: it tells the
    LLM which terms are fair game (and where they come from), and which
    terms are forbidden and where they actually belong. An empty string is
    returned if no scope_terms are configured at all (caller falls back to
    silent omission).
    """
    from scope_resolver import get_grouped_scope_terms

    g = get_grouped_scope_terms(cfg, session["id"], language)
    if not (g["this_session"] or g["prereq"] or g["forbidden"]):
        return ""

    lines: list[str] = []

    def _section(title: str, items: list[tuple[str, str]]):
        lines.append(f"### {title}")
        if items:
            for term, intro in items:
                lines.append(f"- {term} ({intro})")
        else:
            lines.append("- _(none)_")
        lines.append("")

    _section(f"Allowed (this session, {session['id']})", g["this_session"])
    _section("Allowed (from prerequisites)", g["prereq"])
    _section("Forbidden (introduced in later sessions — DO NOT use)", g["forbidden"])
    return "\n".join(lines).rstrip()


def _build_content_boundary_block(cfg: dict, session: dict, language: str) -> str:
    """Build the authoritative Content Boundary block appended at the very
    end of the generation prompt — after batch instructions and course
    materials, so the model sees it as its final instructions before
    producing output.

    Returns an empty string if no scope_terms are configured.
    """
    grouped = _build_scope_terms_grouped_text(cfg, session, language)
    if not grouped:
        return ""
    return (
        "\n\n## Content Boundary (authoritative — read last, applies to every exercise)\n\n"
        "The following lists are derived from the course config's `scope_terms` and\n"
        "`foundational_terms`. They are the authoritative allow / deny list for\n"
        "this batch — they override any incidental mention in the slides.\n\n"
        f"{grouped}\n\n"
        "**Rules**:\n"
        "- An exercise's central topic MUST come from the **Allowed (this session)** list.\n"
        "- Concepts from **Allowed (from prerequisites)** may be used as background or\n"
        "  supporting tools, but not as the exercise's primary subject.\n"
        "- Concepts from **Forbidden (later sessions)** must NOT appear at all,\n"
        "  even if the current session's slides mention them in passing. Those\n"
        "  concepts are reserved for their proper sessions.\n"
    )


def get_inbox_file_paths(cfg: dict, session_id: str) -> list[str]:
    """Return absolute paths to inbox files for a session.

    Checks session-level inbox_files first, then falls back to
    inbox/Slides/{session_id}/*.md auto-detection.
    """
    session = next((s for s in cfg["sessions"] if s["id"] == session_id), None)
    if not session:
        return []

    # Session-level override
    patterns = session.get("inbox_files", [])
    if not patterns:
        # Default: look for inbox/Slides/{session_id}/ and inbox/Slides/{session.dir}/
        inbox_dir = _PROJECT_ROOT / "inbox" / "Slides"
        candidates = [
            inbox_dir / session_id,
            inbox_dir / session["dir"],
        ]
        patterns = []
        for d in candidates:
            if d.is_dir():
                patterns.append(str(d / "*.md"))
                break

    if not patterns:
        return []

    paths = []
    for pat in patterns:
        if not Path(pat).is_absolute():
            pat = str(_PROJECT_ROOT / pat)
        for fpath in sorted(globmod.glob(pat)):
            if Path(fpath).is_file():
                paths.append(str(fpath))
    return paths


def get_inbox_content(cfg: dict, session_id: str, max_chars: int = 200_000) -> str:
    """Read and inline inbox files for a session.

    Checks session-level inbox_files first, then falls back to
    inbox/Slides/{session_id}/*.md auto-detection.
    """
    file_paths = get_inbox_file_paths(cfg, session_id)
    if not file_paths:
        return ""

    parts = []
    total_chars = 0
    for fpath in file_paths:
        try:
            content = Path(fpath).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            parts.append(f"--- {Path(fpath).name} (skipped: {e}) ---")
            continue
        if total_chars + len(content) > max_chars:
            remaining = max_chars - total_chars
            if remaining > 100:
                parts.append(f"--- {Path(fpath).name} (truncated) ---")
                parts.append(content[:remaining])
            parts.append(f"\n[TRUNCATED: inbox content exceeded {max_chars} chars]")
            return "\n\n".join(parts)
        parts.append(f"--- {Path(fpath).name} ---")
        parts.append(content)
        total_chars += len(content)

    return "\n\n".join(parts) if parts else ""


def build_batch_schema(schema_path: Path, exercise_count: int) -> dict:
    """Build a batch-specific JSON schema wrapping exercise schema in an array.

    The schema enforces exactly `exercise_count` items.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    exercise_schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Remove top-level $schema and title — they're for the individual exercise
    item_schema = {k: v for k, v in exercise_schema.items()
                   if k not in ("$schema", "title", "description")}

    return {
        "type": "array",
        "items": item_schema,
        "minItems": exercise_count,
        "maxItems": exercise_count,
    }


def render_generation_prompt(
    cfg: dict,
    session: dict,
    exercise_type: str,
    language: str,
    inbox_content: str = "",
    max_chars: int = 200_000,
    inbox_file_paths: Optional[list[str]] = None,
) -> str:
    """Render the exercise generation prompt for a single type batch.

    If inbox_file_paths is provided, the prompt tells the agent to read files
    from disk (keeps prompt small). Otherwise falls back to inlining inbox_content.
    """
    count = session["type_distribution"][exercise_type]
    primary_lang = cfg["languages"][0]
    secondary_langs = cfg["languages"][1:]

    # For generation, the secondary language is the first non-primary one (for twin_id)
    secondary_lang = secondary_langs[0] if secondary_langs else language

    variables = {
        "course_name_en": cfg.get("course_name_en", cfg["course_id"]),
        "course_name_fr": cfg.get("course_name_fr", cfg["course_id"]),
        "institution": cfg.get("institution", ""),
        "domain": cfg.get("domain", ""),
        "session_id": session["id"],
        "session_title": session.get(f"title_{language}", session["id"]),
        "topics": ", ".join(session["topics"]),
        "prerequisites": ", ".join(session.get("prerequisites", [])) or "None",
        "exercise_count": str(count),
        "primary_language": language,
        "primary_language_name": _lang_name(language),
        "primary_language_upper": language.upper(),
        "secondary_language_upper": secondary_lang.upper(),
        "type_distribution": _build_type_distribution_text({exercise_type: count}),
        "difficulty_distribution": _build_difficulty_distribution_text(cfg),
        "assessment_style": _build_assessment_style_text(cfg),
        "quiz_mode_constraints": _build_quiz_mode_constraints_text(cfg),
        "difficulty_levels": " | ".join(cfg["difficulty_distribution"].keys()),
        "session_title_fields": _build_session_title_fields(cfg, session),
        "max_words": str(cfg["solution_constraints"].get("max_words", 300)),
        "hint_max_words": str(cfg["solution_constraints"].get("hint_max_words", 150)),
        "common_mistakes_types": ", ".join(
            cfg["solution_constraints"].get("common_mistakes_required_for", [])
        ),
        "difficulty_calibration": _build_difficulty_calibration(cfg),
        "software_tool": cfg.get("software_tool", ""),
        "interpretation_template": cfg.get(f"interpretation_template_{language}", ""),
        "scope_terms": _build_scope_terms_text(cfg, session, language),
        "excluded_terms": _build_excluded_terms_text(cfg, session, language),
        "scope_terms_grouped": _build_scope_terms_grouped_text(cfg, session, language),
    }

    template = _read_template("exercise_generation.md")
    text = _resolve_conditionals(template, variables)
    text = _substitute(text, variables)

    # Override: restrict to single type
    type_note = (
        f"\n\n## IMPORTANT: Single-Type Batch\n\n"
        f"Generate EXACTLY **{count}** exercises, ALL of type **{exercise_type}**.\n"
        f"IDs must be `{session['id']}_{language.upper()}_{exercise_type}_001` "
        f"through `{session['id']}_{language.upper()}_{exercise_type}_{count:03d}`.\n"
    )
    text += type_note

    # Provide course materials — prefer file references over inlining
    if inbox_file_paths:
        file_list = "\n".join(f"- `{p}`" for p in inbox_file_paths)
        text += (
            f"\n\n## Course Materials (for reference)\n\n"
            f"Read the following course material files for this session. "
            f"Use the content to ground exercises in real course content.\n\n"
            f"{file_list}\n\n"
            f"**Read each file above** before generating exercises.\n"
        )
    elif inbox_content:
        text += (
            f"\n\n## Course Materials (for reference)\n\n"
            f"Below is the course material for this session. "
            f"Use it to ground exercises in real course content.\n\n"
            f"{inbox_content}\n"
        )

    # Appended LAST so the model reads the authoritative scope deny-list
    # right before producing output.
    text += _build_content_boundary_block(cfg, session, language)

    return text


def render_twin_prompt(
    cfg: dict,
    session: dict,
    exercise_type: str,
    source_language: str,
    target_language: str,
    source_exercises_json: str,
) -> str:
    """Render the twin generation prompt for a single type batch."""
    variables = {
        "source_language_name": _lang_name(source_language),
        "target_language_name": _lang_name(target_language),
        "source_language": source_language,
        "target_language": target_language,
        "source_language_upper": source_language.upper(),
        "target_language_upper": target_language.upper(),
        "course_name_target": cfg.get(f"course_name_{target_language}", cfg["course_id"]),
        "institution": cfg.get("institution", ""),
        "interpretation_template_target": cfg.get(
            f"interpretation_template_{target_language}", ""
        ),
        "glossary_terms": _build_glossary_text(cfg, target_language),
        "exercises_source_json": source_exercises_json,
    }

    template = _read_template("twin_generation.md")
    text = _resolve_conditionals(template, variables)
    text = _substitute(text, variables)
    return text


def render_fix_prompt(
    cfg: dict,
    exercise_json: str,
    findings: list[dict],
) -> str:
    """Render a fix prompt for a single exercise with its findings."""
    findings_text = ""
    for f in findings:
        findings_text += (
            f"- **[{f.get('severity', 'CRITICAL')}]** "
            f"(source: {f.get('source', 'unknown')}): {f.get('description', '')}\n"
        )

    return (
        f"# Exercise Fix Request\n\n"
        f"Fix the following exercise based on the audit findings below.\n"
        f"Output ONLY the corrected exercise as a single JSON object.\n"
        f"Preserve the same ID, twin_id, session, and all structural fields.\n"
        f"Only fix what the findings identify — do not change anything else.\n\n"
        f"## Original Exercise\n\n"
        f"```json\n{exercise_json}\n```\n\n"
        f"## Findings to Fix\n\n{findings_text}\n"
        f"## Output\n\n"
        f"Output the corrected exercise as a single valid JSON object.\n"
    )


def write_prompt_to_temp(content: str, prefix: str = "prompt_") -> Path:
    """Write prompt content to a temp file and return its path."""
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=".txt")
    try:
        os.write(fd, content.encode("utf-8"))
    finally:
        os.close(fd)
    return Path(path)


def write_schema_to_temp(schema: dict, prefix: str = "schema_") -> Path:
    """Write a JSON schema to a temp file and return its path."""
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=".json")
    try:
        os.write(fd, (json.dumps(schema, ensure_ascii=False) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    return Path(path)


def _lang_name(code: str) -> str:
    """Map language code to human name."""
    names = {
        "en": "English",
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ar": "Arabic",
    }
    return names.get(code, code.upper())


# ── New render functions for run.py ──────────────────────────────────────────

def _scale_type_distribution(type_dist: dict, batch_size: int) -> dict:
    """Scale a type distribution proportionally to fit batch_size (largest-remainder method).

    Guarantees all counts >= 0 and sum == batch_size.
    Types with 0 in the original distribution stay at 0.
    """
    total = sum(type_dist.values())
    if total == 0 or total == batch_size:
        return dict(type_dist)

    # Largest-remainder method (Hamilton's method)
    items = list(type_dist.items())
    # Skip types with 0 count
    quotas = []
    for typ, count in items:
        if count == 0:
            quotas.append((typ, 0.0))
        else:
            quotas.append((typ, count * batch_size / total))

    # Floor allocations
    scaled = {typ: int(q) for typ, q in quotas}
    remainders = [(typ, q - int(q)) for typ, q in quotas if q > 0]
    assigned = sum(scaled.values())
    deficit = batch_size - assigned

    # Distribute remaining slots to types with largest fractional remainders
    remainders.sort(key=lambda x: -x[1])
    for i in range(min(deficit, len(remainders))):
        scaled[remainders[i][0]] += 1

    return scaled


def render_full_generation_prompt(
    cfg: dict, session: dict, language: str,
    loop_index: int, batch_size: int, id_offset: int,
    inbox_content: str = "",
) -> str:
    """Render generation prompt for a full batch (all types, proportional distribution).

    loop_index: 1-based loop number
    batch_size: exercises per loop (default 20)
    id_offset: starting ID number (e.g., 1, 21, 41)
    """
    primary_lang = cfg["languages"][0]
    secondary_langs = cfg["languages"][1:]
    secondary_lang = secondary_langs[0] if secondary_langs else language

    # Scale type distribution to batch_size
    batch_dist = _scale_type_distribution(session["type_distribution"], batch_size)

    variables = {
        "course_name_en": cfg.get("course_name_en", cfg["course_id"]),
        "course_name_fr": cfg.get("course_name_fr", cfg["course_id"]),
        "institution": cfg.get("institution", ""),
        "domain": cfg.get("domain", ""),
        "session_id": session["id"],
        "session_title": session.get(f"title_{language}", session["id"]),
        "topics": ", ".join(session["topics"]),
        "prerequisites": ", ".join(session.get("prerequisites", [])) or "None",
        "exercise_count": str(batch_size),
        "primary_language": language,
        "primary_language_name": _lang_name(language),
        "primary_language_upper": language.upper(),
        "secondary_language_upper": secondary_lang.upper(),
        "type_distribution": _build_type_distribution_text(batch_dist),
        "difficulty_distribution": _build_difficulty_distribution_text(cfg),
        "assessment_style": _build_assessment_style_text(cfg),
        "quiz_mode_constraints": _build_quiz_mode_constraints_text(cfg),
        "difficulty_levels": " | ".join(cfg["difficulty_distribution"].keys()),
        "session_title_fields": _build_session_title_fields(cfg, session),
        "max_words": str(cfg["solution_constraints"].get("max_words", 300)),
        "hint_max_words": str(cfg["solution_constraints"].get("hint_max_words", 150)),
        "common_mistakes_types": ", ".join(
            cfg["solution_constraints"].get("common_mistakes_required_for", [])
        ),
        "difficulty_calibration": _build_difficulty_calibration(cfg),
        "software_tool": cfg.get("software_tool", ""),
        "interpretation_template": cfg.get(f"interpretation_template_{language}", ""),
        "scope_terms": _build_scope_terms_text(cfg, session, language),
        "excluded_terms": _build_excluded_terms_text(cfg, session, language),
        "scope_terms_grouped": _build_scope_terms_grouped_text(cfg, session, language),
    }

    template = _read_template("exercise_generation.md")
    text = _resolve_conditionals(template, variables)
    text = _substitute(text, variables)

    # Add batch-specific instructions with concrete ID example
    id_end = id_offset + batch_size - 1
    first_type = list(session["type_distribution"].keys())[0]
    example_id = f"{session['id']}_{language.upper()}_{first_type}_{id_offset:03d}"
    batch_note = (
        f"\n\n## Batch Instructions\n\n"
        f"This is batch {loop_index}. Generate exactly **{batch_size}** exercises "
        f"with the type distribution above.\n\n"
        f"**ID numbering**: Use numbers `{id_offset:03d}` through `{id_end:03d}`.\n"
        f"Example: `{example_id}`\n\n"
        f"Distribute the {batch_size} exercises across ALL types as specified above.\n"
    )
    text += batch_note

    # Inline inbox content if provided, otherwise auto-detect
    if not inbox_content:
        inbox_content = get_inbox_content(cfg, session["id"])
    if inbox_content:
        text += (
            f"\n\n## Course Materials (for reference)\n\n"
            f"Below is the course material for this session. "
            f"Use it to ground exercises in real course content.\n\n"
            f"{inbox_content}\n"
        )

    # Appended LAST so the model reads the authoritative scope deny-list
    # right before producing output.
    text += _build_content_boundary_block(cfg, session, language)

    return text


def render_full_twin_prompt(
    cfg: dict, session: dict, source_lang: str,
    target_lang: str, source_json: str,
) -> str:
    """Render twin prompt for a full batch of exercises."""
    variables = {
        "source_language_name": _lang_name(source_lang),
        "target_language_name": _lang_name(target_lang),
        "source_language": source_lang,
        "target_language": target_lang,
        "source_language_upper": source_lang.upper(),
        "target_language_upper": target_lang.upper(),
        "course_name_target": cfg.get(f"course_name_{target_lang}", cfg["course_id"]),
        "institution": cfg.get("institution", ""),
        "interpretation_template_target": cfg.get(
            f"interpretation_template_{target_lang}", ""
        ),
        "glossary_terms": _build_glossary_text(cfg, target_lang),
        "exercises_source_json": source_json,
    }

    template = _read_template("twin_generation.md")
    text = _resolve_conditionals(template, variables)
    text = _substitute(text, variables)
    return text


def render_self_audit_prompt(
    cfg: dict, session: dict, exercises_json: str,
) -> str:
    """Render combined math+pedagogy audit prompt for Claude."""
    primary = cfg["languages"][0]
    variables = {
        "session_id": session["id"],
        "session_title": session.get(f"title_{primary}", session["id"]),
        "max_words": str(cfg["solution_constraints"].get("max_words", 300)),
        "hints_min": str(cfg["solution_constraints"].get("hints_min", 2)),
        "hints_max": str(cfg["solution_constraints"].get("hints_max", 3)),
        "hint_max_words": str(cfg["solution_constraints"].get("hint_max_words", 150)),
        "common_mistakes_types": ", ".join(
            cfg["solution_constraints"].get("common_mistakes_required_for", [])
        ),
        "difficulty_calibration": _build_difficulty_calibration(cfg),
        "interpretation_template": cfg.get(
            f"interpretation_template_{primary}", ""
        ),
        "glossary_terms": _build_glossary_text(cfg, cfg["languages"][1]) if len(cfg["languages"]) > 1 else "(single language)",
        "scope_terms_with_introduction_session": _build_scope_terms_grouped_text(
            cfg, session, primary,
        ),
    }

    template = _read_template("self_audit.md")
    text = _resolve_conditionals(template, variables)
    text = _substitute(text, variables)

    # Inline exercises
    text += (
        f"\n\n## Exercises to Audit\n\n"
        f"```json\n{exercises_json}\n```\n"
    )

    return text


def render_codex_audit_prompt(cfg: dict, session: dict) -> str:
    """Render codex audit prompt with file paths (codex reads from disk)."""
    output_dir = str(_PROJECT_ROOT / "output" / cfg["course_id"])
    session_dir = session["dir"]

    template = _read_template("codex_audit.md")

    primary = cfg["languages"][0]
    grouped_text = _build_scope_terms_grouped_text(cfg, session, primary)
    twin_lang = cfg["languages"][1] if len(cfg["languages"]) > 1 else None
    glossary_text = (
        _build_glossary_text(cfg, twin_lang) if twin_lang else "(single language)"
    )

    # Codex uses {VARIABLE} style placeholders
    replacements = {
        "{OUTPUT_DIR}": output_dir,
        "{SESSION_DIR}": session_dir,
        "{MAX_WORDS}": str(cfg["solution_constraints"].get("max_words", 300)),
        "{HINTS_MIN}": str(cfg["solution_constraints"].get("hints_min", 2)),
        "{HINTS_MAX}": str(cfg["solution_constraints"].get("hints_max", 3)),
        "{HINT_MAX_WORDS}": str(cfg["solution_constraints"].get("hint_max_words", 150)),
        "{COMMON_MISTAKES_TYPES}": ", ".join(
            cfg["solution_constraints"].get("common_mistakes_required_for", [])
        ),
        "{DIFFICULTY_CALIBRATION}": _build_difficulty_calibration(cfg),
        "{SCOPE_TERMS_WITH_INTRODUCTION_SESSION}": grouped_text or "(no scope_terms configured)",
        "{GLOSSARY_TERMS}": glossary_text,
    }

    text = template
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)

    return text
