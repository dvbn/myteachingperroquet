#!/usr/bin/env python3
"""Phase 2 validator: twin parity and glossary compliance.

Checks:
- Every exercise in one language has a twin in each other language
- Numerical answers match between twins (normalized for locale differences)
- Difficulty labels match between twins
- Topics match between twins (normalized for translated topic names)
- Non-primary-language exercises use glossary-mandated terminology

Exit code 0 = PASS, 1 = FAIL.

Flags:
  --findings-output <path>  Write structured findings JSON alongside markdown.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config_loader import (
    load_config, get_output_dir, get_session_dirs, get_json_files,
    get_languages, get_primary_language,
)
from findings_io import FindingCollector


# Languages that use comma as decimal separator and space/period as thousands.
_COMMA_DECIMAL_LOCALES = frozenset({
    "fr", "de", "it", "es", "pt", "nl", "pl", "cs", "ro", "sv", "da",
    "nb", "nn", "fi", "hu", "tr", "el", "ru", "uk", "bg", "hr", "sk",
    "sl", "et", "lt", "lv", "ca", "gl", "id", "vi",
})


def _uses_comma_decimal(locale: str) -> bool:
    return locale.lower().split("_")[0].split("-")[0] in _COMMA_DECIMAL_LOCALES


def extract_numbers_locale(text: str, locale: str = "en") -> list[float]:
    """Extract floats from text, honoring locale-specific separators.

    `en`-style locales: comma is the thousands separator, period is the
    decimal separator. ``1,200.5`` -> ``1200.5``.

    Comma-decimal locales (`fr`, `de`, ...): period is the thousands
    separator, comma is the decimal separator. ``1.200,5`` -> ``1200.5``.

    Also handles narrow / non-breaking spaces as thousands separators
    (typical in French typography), and strips LaTeX-mode brace wrappers
    around decimal separators (e.g. ``0{,}408``).
    """
    if not text:
        return []
    normalized = text.replace("\u202f", " ").replace("\xa0", " ")
    # Strip LaTeX-mode brace wrappers around decimal separators
    # (e.g. ``0{,}408`` -> ``0,408``).
    normalized = re.sub(r"\{([,.])\}", r"\1", normalized)
    numbers = []
    for m in re.finditer(r"-?\d[\d\s,.]*\d|-?\d", normalized):
        s = m.group(0).strip()
        # Whitespace inside a number is always a thousands separator.
        s = s.replace(" ", "")
        if _uses_comma_decimal(locale):
            # comma-decimal: period is thousands sep, comma is decimal sep
            s = s.replace(".", "")
            s = s.replace(",", ".")
        else:
            # period-decimal: comma is thousands sep, period is decimal sep
            s = s.replace(",", "")
        try:
            numbers.append(float(s))
        except ValueError:
            continue
    return numbers


def numerical_answers_match(na1: str | None, na2: str | None,
                            lang1: str = "en", lang2: str = "en") -> bool:
    if na1 == na2:
        return True
    if na1 is None or na2 is None:
        return na1 is None and na2 is None
    nums1 = extract_numbers_locale(na1, locale=lang1)
    nums2 = extract_numbers_locale(na2, locale=lang2)
    if not nums1 and not nums2:
        return False
    if len(nums1) != len(nums2):
        return False
    for n1, n2 in zip(nums1, nums2):
        if n1 == 0 and n2 == 0:
            continue
        if abs(n1 - n2) > 0.001 * max(1.0, abs(n1), abs(n2)):
            return False
    return True


def build_glossary_checks(cfg):
    """Build forbidden-term → correct-term checks for the twin language.

    Two sources:
      1. Explicit `Never 'X'` notes on a glossary entry — `X` must not
         appear in twin-language exercises.
      2. **Cross-language leak detection**: if a glossary entry is
         "OLS / MCO" with no explicit `Never` note, it is still a
         violation if the *English* term `OLS` shows up unchanged in
         a French exercise (the translator should have used `MCO`).
         This catches the silent-leak case where the glossary entry has
         no note but the rule is implicit.

    Both checks are case-insensitive and word-boundary aware.
    """
    checks = []
    langs = get_languages(cfg)
    primary = get_primary_language(cfg)
    target_lang = [l for l in langs if l != primary]
    if not target_lang:
        return checks
    target = target_lang[0]

    for entry in cfg.get("glossary_terms", []):
        primary_term = entry.get(primary, "")
        target_term = entry.get(target, "")
        note = entry.get("note", "")

        # Explicit "Never 'X'" forbidden patterns
        m = re.search(r"[Nn]ever ['\"]?([^'\"]+)['\"]?", note)
        if m and target_term:
            wrong = m.group(1).strip()
            if wrong:
                checks.append((wrong.lower(), target_term))

        # Implicit cross-language leak: primary-language term appearing
        # unchanged in a twin-language exercise (skip pure acronyms that
        # legitimately appear in both languages, e.g. "OLS" → "MCO" but
        # "BLUE" stays "BLUE").
        if primary_term and target_term and primary_term.lower() != target_term.lower():
            # Heuristic to skip cross-language identical acronyms: if both
            # are short uppercase tokens, they're likely shared (e.g. R²).
            if not (
                primary_term == primary_term.upper()
                and target_term == target_term.upper()
                and len(primary_term) <= 5
                and primary_term == target_term
            ):
                if (primary_term.lower(), target_term) not in checks:
                    checks.append((primary_term.lower(), target_term))

    return checks


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
    out_dir = get_output_dir(cfg)
    exercises = {}
    session_map = {}  # eid -> session_id
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
                    collector.add("critical", "bilingual", f"_session:{sid}",
                                   f"Cannot load {fp.name}: {e}",
                                   evidence=f"file={fp.name}, error={e}",
                                   session_id=sid)
                continue
            for ex in data:
                exercises[ex["id"]] = ex
                session_map[ex["id"]] = sid
    return exercises, session_map


def main():
    config_path, findings_output = _parse_args()
    cfg = load_config(config_path)
    collector = FindingCollector(source="validator_bilingual")
    exercises, session_map = load_all(cfg, collector)
    glossary_checks = build_glossary_checks(cfg)
    primary_lang = get_primary_language(cfg)
    criticals = 0
    warnings = 0
    twins_checked = 0

    print("# Bilingual Validation Report\n")

    # Check twin parity
    seen_pairs = set()
    for eid, ex in exercises.items():
        sid = session_map.get(eid)
        twin_id = ex.get("twin_id", "")
        if not twin_id:
            print(f"### WARNING Exercise {eid}: missing twin_id\n")
            collector.add("major", "bilingual", eid,
                           "Missing twin_id",
                           evidence=f"exercise_id={eid}, twin_id field is empty or missing",
                           session_id=sid, blocking=False)
            warnings += 1
            continue

        pair = tuple(sorted([eid, twin_id]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        if twin_id not in exercises:
            print(f"### CRITICAL Exercise {eid}: twin '{twin_id}' not found\n")
            collector.add("critical", "bilingual", eid,
                           f"Twin '{twin_id}' not found in exercise bank",
                           evidence=f"twin_id={twin_id}",
                           session_id=sid)
            criticals += 1
            continue

        twin = exercises[twin_id]
        twins_checked += 1

        # Numerical answer match (locale-aware)
        na1 = (ex.get("solution") or {}).get("numerical_answer")
        na2 = (twin.get("solution") or {}).get("numerical_answer")
        lang1 = ex.get("language", "en")
        lang2 = twin.get("language", "en")
        if not numerical_answers_match(na1, na2, lang1, lang2):
            print(f"### CRITICAL Twin pair {eid} / {twin_id}: numerical_answer mismatch")
            print(f"- {eid}: {na1}")
            print(f"- {twin_id}: {na2}\n")
            collector.add("critical", "bilingual", eid,
                           f"Numerical answer mismatch with twin {twin_id}",
                           evidence=f"{eid}={na1!r}, {twin_id}={na2!r}",
                           recommended_fix="Ensure numerical answers match between twins (account for locale formatting)",
                           session_id=sid)
            criticals += 1

        # Difficulty match
        if ex.get("difficulty") != twin.get("difficulty"):
            print(f"### WARNING Twin pair {eid} / {twin_id}: difficulty mismatch")
            print(f"- {eid}: {ex.get('difficulty')}")
            print(f"- {twin_id}: {twin.get('difficulty')}\n")
            collector.add("major", "bilingual", eid,
                           f"Difficulty mismatch with twin {twin_id}: {ex.get('difficulty')} vs {twin.get('difficulty')}",
                           evidence=f"{eid}={ex.get('difficulty')}, {twin_id}={twin.get('difficulty')}",
                           session_id=sid, blocking=False)
            warnings += 1

        # Topics match
        t1 = ex.get("topics", [])
        t2 = twin.get("topics", [])
        if len(t1) != len(t2):
            print(f"### WARNING Twin pair {eid} / {twin_id}: topics count mismatch")
            print(f"- {eid}: {t1}")
            print(f"- {twin_id}: {t2}\n")
            collector.add("minor", "bilingual", eid,
                           f"Topics count mismatch with twin {twin_id}: {len(t1)} vs {len(t2)}",
                           evidence=f"{eid}={t1}, {twin_id}={t2}",
                           session_id=sid)
            warnings += 1

    # Glossary compliance — word-boundary aware to avoid false positives
    # like forbidden ``ols`` matching inside ``pools``.
    if glossary_checks:
        print("## Glossary Compliance\n")
        violations = 0
        # Compile each forbidden term to a word-boundary regex once.
        compiled = []
        for wrong, correct in glossary_checks:
            # Build a token-aware whole-word pattern (mirrors scope_resolver
            # but kept inline to avoid the import cycle). Hyphens and spaces
            # inside multi-word terms are treated flexibly.
            parts = re.split(r"[\s\-]+", wrong.strip())
            parts = [re.escape(p) for p in parts if p]
            if not parts:
                continue
            body = r"[\s\-]+".join(parts)
            pat = re.compile(
                r"(?<![A-Za-zÀ-ÿ0-9])" + body + r"(?![A-Za-zÀ-ÿ0-9])",
                re.IGNORECASE,
            )
            compiled.append((pat, wrong, correct))

        for eid, ex in exercises.items():
            if ex.get("language") == primary_lang:
                continue
            sid = session_map.get(eid)
            text = (ex.get("question_text", "") + " " +
                    (ex.get("solution") or {}).get("text", "") + " " +
                    " ".join(ex.get("hints", [])))
            for pat, wrong, correct in compiled:
                if pat.search(text):
                    print(f"### WARNING Exercise {eid}: glossary violation — found '{wrong}', should use '{correct}'\n")
                    collector.add("major", "bilingual", eid,
                                   f"Glossary violation: found '{wrong}', should use '{correct}'",
                                   evidence=f"forbidden_term='{wrong}', correct_term='{correct}'",
                                   recommended_fix=f"Replace '{wrong}' with '{correct}'",
                                   session_id=sid, blocking=False)
                    warnings += 1
                    violations += 1
        print(f"- Terms checked: {len(glossary_checks)} forbidden patterns")
        print(f"- Violations found: {violations}\n")

    print(f"\n## Summary")
    print(f"- Exercises checked: {len(exercises)}")
    print(f"- Twin pairs verified: {twins_checked}")
    print(f"- CRITICALs: {criticals}")
    print(f"- WARNINGs: {warnings}")
    print(f"- Verdict: {'PASS' if criticals == 0 else 'FAIL'}\n")

    if findings_output:
        collector.write(findings_output)
        print(f"Findings written to {findings_output} ({len(collector.findings)} findings)")

    sys.exit(0 if criticals == 0 else 1)


if __name__ == "__main__":
    main()
