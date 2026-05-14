#!/usr/bin/env python3
"""Generate glossary_FR_EN.md from course_config.json glossary_terms.

Produces a bilingual markdown glossary grouped by category. Runs as part
of Phase 5 (catalog generation) or standalone.

Usage:
    python3 pipeline/glossary_generator.py                  # default config
    python3 pipeline/glossary_generator.py path/to/config   # custom config
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import load_config, get_output_dir

# Category assignment: keyword → category name
_CATEGORY_KEYWORDS = {
    "Variables & Data / Variables et données": [
        "variable", "data", "sample", "cross-section", "time series",
        "panel", "repeated",
    ],
    "Regression / Régression": [
        "intercept", "slope", "multicollinearity", "goodness",
        "prediction error",
    ],
    "Tests / Tests statistiques": [
        "hypothesis", "null", "alternative", "critical value",
        "significance", "confidence", "degrees of freedom",
    ],
    "Functional Forms / Formes fonctionnelles": [
        "elasticity", "interaction", "z-score",
    ],
    "Assumption Violations / Violations des hypothèses": [
        "heteroskedasticity", "homoskedasticity", "autocorrelation",
        "gls", "wls", "fgls", "spurious",
    ],
    "Advanced Methods / Méthodes avancées": [
        "2sls", "endogen", "exogen", "instrumental", "exclusion",
        "relevance", "simultaneity", "reverse", "measurement",
        "attenuation", "treatment", "counterfactual", "common trend",
        "fixed effect", "difference-in-diff",
    ],
}

# Fallback category
_DEFAULT_CATEGORY = "General Econometrics / Économétrie générale"


def _categorize_term(term_en: str) -> str:
    """Assign a term to a category based on keyword matching."""
    en_lower = term_en.lower()
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in en_lower:
                return cat
    return _DEFAULT_CATEGORY


def generate_glossary_md(cfg: dict) -> str:
    """Build glossary markdown string from glossary_terms in config."""
    terms = cfg.get("glossary_terms", [])
    if not terms:
        return ""

    # Group by category, preserving config order within each category
    categories: dict[str, list[dict]] = {}
    # Initialize with ordered keys
    for cat in [_DEFAULT_CATEGORY] + list(_CATEGORY_KEYWORDS.keys()):
        categories[cat] = []

    for term in terms:
        cat = _categorize_term(term["en"])
        categories[cat].append(term)

    lines = ["# Glossaire bilingue / Bilingual Glossary", ""]

    for cat, cat_terms in categories.items():
        if not cat_terms:
            continue
        lines.append(f"## {cat}")
        lines.append("")
        lines.append("| English | Français | Notes |")
        lines.append("|---------|----------|-------|")
        for t in cat_terms:
            en = t["en"]
            fr = t["fr"]
            note = t.get("note", "")
            lines.append(f"| {en} | {fr} | {note} |")
        lines.append("")

    return "\n".join(lines)


def generate_glossary_json(cfg: dict) -> dict:
    """Build a machine-readable glossary dict for downstream RAG ingestion.

    Returns:
        {
            "terminology_fr": "Termes: OLS→MCO, Unbiased→Sans biais, ...",
            "abbreviations": {"ols": "mco", ...},
            "terms": [{"en": ..., "fr": ..., "note": ...}, ...]
        }
    """
    terms = cfg.get("glossary_terms", [])
    if not terms:
        return {"terminology_fr": "", "abbreviations": {}, "terms": []}

    # Build terminology_fr string
    pairs = [f"{t['en']}→{t['fr']}" for t in terms]
    terminology_fr = "Termes: " + ", ".join(pairs)

    # Build abbreviations map (lowercase, single-token keys only for BM25 expansion)
    abbreviations = {}
    for t in terms:
        en_lower = t["en"].lower()
        fr_lower = t["fr"].lower()
        # Only include single-word or acronym keys (multi-word keys won't match
        # token-level lookup in downstream RAG query expansion)
        if " " not in en_lower:
            abbreviations[en_lower] = fr_lower

    return {
        "terminology_fr": terminology_fr,
        "abbreviations": abbreviations,
        "terms": terms,
    }


def main():
    cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else None)
    out_dir = get_output_dir(cfg)

    print(f"Generating glossary for {cfg['course_id']}...")

    # File suffix is built from configured languages so non-EN/FR pairs
    # don't get a misleading "FR_EN" filename. Order: secondary → primary
    # (matches the historical "twin → primary" reading direction).
    languages = cfg.get("languages", ["en"])
    if len(languages) >= 2:
        suffix = f"{languages[1].upper()}_{languages[0].upper()}"
    else:
        suffix = languages[0].upper()

    # Markdown glossary
    md = generate_glossary_md(cfg)
    md_path = out_dir / f"glossary_{suffix}.md"
    md_path.write_text(md + "\n", encoding="utf-8")
    term_count = len(cfg.get("glossary_terms", []))
    print(f"  {md_path}: {term_count} terms")

    # Machine-readable JSON glossary
    gj = generate_glossary_json(cfg)
    json_path = out_dir / f"glossary_{suffix}.json"
    json_path.write_text(
        json.dumps(gj, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"  {json_path}: {len(gj['abbreviations'])} abbreviation pairs")

    print("Done.")


if __name__ == "__main__":
    main()
