#!/usr/bin/env python3
"""Phase 2 validator: math verification via SymPy (+ optional scipy.stats).

For each exercise with numerical_answer + key_formula:
1. Parse key_formula LaTeX -> SymPy expression
2. Extract variable values from question_text (regex: "x = 50", "a = 2.5", etc.)
3. Substitute and evaluate
4. Compare to numerical_answer with tolerance
5. Optional domain-specific checks (e.g., statistical critical values) — config-gated
6. Graceful degradation: parse failures -> WARNING, not CRITICAL

Dependencies: sympy (required), scipy (optional, for statistical checks)
Exit code 0 = PASS, 1 = FAIL.

Flags:
  --findings-output <path>  Write structured findings JSON alongside markdown.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config_loader import load_config, get_output_dir, get_session_dirs, get_json_files
from findings_io import FindingCollector

try:
    import sympy
    from sympy.parsing.latex import parse_latex
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

try:
    from scipy import stats as sp_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# Reuse the locale-aware parser from validate_bilingual so a comma-decimal
# answer like "0,42" doesn't silently become 0.0 here.
from validate_bilingual import extract_numbers_locale, _uses_comma_decimal


def _normalize_numeric_token(token: str, lang: str) -> str:
    """Normalize a single numeric token (no surrounding text) to dot-decimal."""
    s = token.replace(" ", "").replace("\xa0", "").replace(" ", "")
    if _uses_comma_decimal(lang):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    return s


def extract_numbers(text: str, lang: str = "en") -> dict[str, float]:
    """Extract `name = value` pairs from text, locale-aware on the value.

    Two patterns:
      - bare ``name = value`` (with optional LaTeX-y characters in `name`)
      - LaTeX-mode ``$name = value$``
    `value` may be in en (``1,200.5``) or comma-decimal (``1.200,5`` /
    ``1{,}5``) form.
    """
    values: dict[str, float] = {}
    # Strip LaTeX brace wrappers around decimal separators first
    normalized = re.sub(r"\{([,.])\}", r"\1", text)
    # The numeric token regex is permissive — we try to coerce after.
    num_pat = r"-?\d[\d\s,.]*\d|-?\d"
    for m in re.finditer(rf"(\w[\w^{{}}]*)\s*=\s*({num_pat})(?:[eE][+\-]?\d+)?", normalized):
        name = m.group(1).lower().replace("^", "").replace("{", "").replace("}", "")
        try:
            values[name] = float(_normalize_numeric_token(m.group(2), lang))
        except ValueError:
            continue
    for m in re.finditer(rf"\$\s*(\w+)\s*=\s*({num_pat})\s*\$", normalized):
        name = m.group(1).lower()
        try:
            values[name] = float(_normalize_numeric_token(m.group(2), lang))
        except ValueError:
            continue
    return values


def try_parse_numerical(answer_str: str, lang: str = "en") -> float | None:
    """Locale-aware numeric parsing of an exercise's `numerical_answer`."""
    if not answer_str:
        return None
    nums = extract_numbers_locale(answer_str, locale=lang)
    if nums:
        return nums[0]
    return None


def check_tolerance(computed: float, expected: float, rtol: float, atol: float) -> bool:
    if expected == 0:
        return abs(computed) < atol
    rel_err = abs(computed - expected) / max(1.0, abs(expected))
    abs_err = abs(computed - expected)
    return rel_err < rtol or abs_err < atol


def validate_exercise_math(ex: dict, rtol: float, atol: float,
                           checks: list[str] | None = None) -> list[tuple[str, str, str | None]]:
    """Validate one exercise's math. Returns list of (severity, message, evidence)."""
    if checks is None:
        checks = ["formula_eval"]
    findings = []
    eid = ex.get("id", "unknown")
    sol = ex.get("solution") or {}
    formula = sol.get("key_formula")
    answer_str = sol.get("numerical_answer")
    lang = (ex.get("language") or "en").lower()

    if not answer_str:
        return findings

    expected = try_parse_numerical(answer_str, lang=lang)
    if expected is None:
        findings.append(("minor", f"Exercise {eid}: cannot parse numerical_answer '{answer_str}'",
                          f"numerical_answer='{answer_str}'"))
        return findings

    if "formula_eval" in checks and formula and HAS_SYMPY:
        try:
            expr = parse_latex(formula)
            values = extract_numbers(ex.get("question_text", ""), lang=lang)
            if values:
                free = expr.free_symbols
                subs = {}
                for sym in free:
                    name = str(sym).lower()
                    if name in values:
                        subs[sym] = values[name]

                if subs and len(subs) == len(free):
                    computed = float(expr.subs(subs).evalf())
                    if not check_tolerance(computed, expected, rtol, atol):
                        findings.append((
                            "critical",
                            f"Exercise {eid}: math mismatch — formula evaluates to {computed:.6g}, "
                            f"expected {expected:.6g} (rtol={rtol}, atol={atol})",
                            f"formula='{formula}', computed={computed:.6g}, expected={expected:.6g}, vars={values}"
                        ))
                else:
                    findings.append((
                        "minor",
                        f"Exercise {eid}: could not substitute all variables — "
                        f"free={[str(s) for s in free]}, found={list(subs.keys())}",
                        f"free_symbols={[str(s) for s in free]}, matched={list(subs.keys())}"
                    ))
        except Exception as e:
            findings.append((
                "minor",
                f"Exercise {eid}: LaTeX parse/eval failed — {type(e).__name__}: {e}",
                f"formula='{formula}', error={type(e).__name__}: {e}"
            ))

    if "t_critical_values" in checks and HAS_SCIPY:
        qt = ex.get("question_text", "") + " " + sol.get("text", "")
        for m in re.finditer(r"t[_\s]*(?:crit|critical|α)[^=]*=\s*(-?\d+\.?\d*)", qt, re.IGNORECASE):
            stated_t = float(m.group(1))
            df_match = re.search(r"(?:df|d\.d\.l\.?|degrees?\s+of\s+freedom)\s*=\s*(\d+)", qt, re.IGNORECASE)
            alpha_match = re.search(r"(?:α|alpha|significance)\s*=?\s*(0\.\d+)", qt, re.IGNORECASE)
            if df_match and alpha_match:
                df = int(df_match.group(1))
                alpha = float(alpha_match.group(1))
                expected_t = abs(sp_stats.t.ppf(alpha / 2, df))
                if not check_tolerance(abs(stated_t), expected_t, rtol * 2, atol * 2):
                    findings.append((
                        "major",
                        f"Exercise {eid}: t critical value {stated_t} may be incorrect "
                        f"(expected ±{expected_t:.4f} for df={df}, α={alpha})",
                        f"stated_t={stated_t}, expected_t={expected_t:.4f}, df={df}, alpha={alpha}"
                    ))

    return findings


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
    math_cfg = cfg.get("math_validation", {})
    rtol = math_cfg.get("tolerance_relative", 0.02)
    atol = math_cfg.get("tolerance_absolute", 0.05)
    checks = math_cfg.get("checks", ["formula_eval"])
    criticals = 0
    warnings = 0
    verified = 0
    skipped = 0
    collector = FindingCollector(source="validator_math")

    print("# Math Validation Report\n")
    print(f"Enabled checks: {checks}\n")

    # Hard-fail if a configured check has no backing dependency. The
    # previous behaviour silently downgraded to PASS, so a clean-env
    # install missing sympy/antlr4 would let the bank ship without ever
    # actually verifying any formula.
    missing_deps = []
    if not HAS_SYMPY and "formula_eval" in checks:
        missing_deps.append("sympy + antlr4-python3-runtime (for formula_eval)")
    if not HAS_SCIPY and "t_critical_values" in checks:
        missing_deps.append("scipy (for t_critical_values)")
    if missing_deps:
        print("FAIL: math_validation.checks lists checks whose dependencies are missing:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("Install via: pip install -r requirements.txt")
        print("Or remove the affected check from course_config.json math_validation.checks.")
        print("\n## Summary")
        print("- Verdict: FAIL\n")
        sys.exit(1)

    for sid, sdir in get_session_dirs(cfg).items():
        for jf in get_json_files(cfg):
            fp = out_dir / sdir / jf
            if not fp.exists():
                continue
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                collector.add("critical", "math", f"_session:{sid}",
                               f"Cannot load {fp.name}: {e}",
                               evidence=f"file={fp.name}, error={e}",
                               session_id=sid)
                criticals += 1
                continue

            for ex in data:
                sol = ex.get("solution") or {}
                if not sol.get("numerical_answer"):
                    skipped += 1
                    continue

                eid = ex.get("id", "unknown")
                findings = validate_exercise_math(ex, rtol, atol, checks)
                if not findings:
                    verified += 1
                for severity, msg, evidence in findings:
                    # Map to markdown severity for backward compat
                    md_sev = severity.upper() if severity != "minor" else "WARNING"
                    print(f"### {md_sev} {msg}\n")
                    if severity == "critical":
                        criticals += 1
                    else:
                        warnings += 1

                    collector.add(severity, "math", eid, msg,
                                   evidence=evidence, session_id=sid)

    print(f"\n## Summary")
    print(f"- Exercises with numerical_answer: {verified + criticals + warnings}")
    print(f"- Verified OK: {verified}")
    print(f"- Skipped (no numerical_answer): {skipped}")
    print(f"- CRITICALs: {criticals}")
    print(f"- WARNINGs: {warnings}")
    print(f"- Verdict: {'PASS' if criticals == 0 else 'FAIL'}\n")

    if findings_output:
        collector.write(findings_output)
        print(f"Findings written to {findings_output} ({len(collector.findings)} findings)")

    sys.exit(0 if criticals == 0 else 1)


if __name__ == "__main__":
    main()
