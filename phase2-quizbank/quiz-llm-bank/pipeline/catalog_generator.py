#!/usr/bin/env python3
"""Generate EXERCISE_BANK_CATALOG.md from assembled exercise files.

Runs after postprocessor.py. Reads all exercises_EN.json files (EN only,
since FR are twins) and produces a comprehensive markdown catalog for
browsing, filtering, and keep/discard decisions.

Usage:
    python3 pipeline/catalog_generator.py                  # default config
    python3 pipeline/catalog_generator.py path/to/config   # custom config
"""

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import load_config, get_output_dir, get_session_path


def load_all_exercises(cfg: dict) -> dict[str, list[dict]]:
    """Load EN exercises for every session. Returns {session_id: [exercises]}."""
    primary = cfg["languages"][0].upper()
    result = {}
    for session in cfg["sessions"]:
        sid = session["id"]
        fpath = get_session_path(cfg, sid) / f"exercises_{primary}.json"
        if fpath.exists():
            result[sid] = json.loads(fpath.read_text(encoding="utf-8"))
        else:
            result[sid] = []
    return result


def extract_keywords(texts: list[str], top_n: int = 20) -> list[tuple[str, int]]:
    """Extract most frequent substantive words from a list of texts."""
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "shall",
        "should", "may", "might", "must", "can", "could", "of", "in", "to",
        "for", "with", "on", "at", "from", "by", "as", "into", "through",
        "during", "before", "after", "above", "below", "between", "under",
        "again", "further", "then", "once", "here", "there", "when", "where",
        "why", "how", "all", "each", "every", "both", "few", "more", "most",
        "other", "some", "such", "no", "nor", "not", "only", "own", "same",
        "than", "too", "very", "just", "because", "but", "and", "or", "if",
        "while", "about", "up", "out", "so", "what", "which", "who", "whom",
        "this", "that", "these", "those", "it", "its", "he", "she", "they",
        "we", "you", "your", "his", "her", "their", "our", "my", "me", "him",
        "them", "us", "also", "using", "given", "following", "consider",
        "suppose", "let", "use", "show", "find", "determine", "explain",
        "describe", "based", "true", "false", "data", "model", "regression",
        "variable", "variables", "coefficient", "coefficients", "value",
        "values", "test", "result", "results", "output", "stata", "command",
        "exercise", "question", "answer", "solution", "example",
    }
    words = Counter()
    for text in texts:
        cleaned = re.sub(r'[\\${}^_\d\[\]().,;:!?"\'/|=+<>~`*#@&%]', " ", text.lower())
        for w in cleaned.split():
            if len(w) >= 3 and w not in stopwords and not w.startswith("\\"):
                words[w] += 1
    return words.most_common(top_n)


def generate_catalog(cfg: dict) -> str:
    """Build the full catalog markdown string."""
    all_exercises = load_all_exercises(cfg)
    out_dir = get_output_dir(cfg)
    lines = []

    def w(line=""):
        lines.append(line)

    # Flatten all exercises
    all_flat = []
    for sid, exs in all_exercises.items():
        all_flat.extend(exs)

    total = len(all_flat)
    total_both = total * len(cfg["languages"])

    # --- Header ---
    w(f"# Exercise Bank Catalog -- {cfg.get('course_name_en', cfg['course_id'])}")
    w()
    w(f"> **Generated**: {date.today().isoformat()}  ")
    w(f"> **Source directory**: `output/{cfg['course_id']}/`  ")
    w(f"> **Sessions**: {cfg['sessions'][0]['id']}--{cfg['sessions'][-1]['id']}  ")
    langs = ", ".join(lang.upper() for lang in cfg["languages"])
    w(f"> **Languages**: {langs}")
    w()
    w("---")
    w()

    # --- TOC ---
    w("## Table of Contents")
    w()
    w("1. [Executive Summary](#1-executive-summary)")
    w("2. [Per-Session Overview](#2-per-session-overview)")
    w("3. [Master Topic Index](#3-master-topic-index)")
    w("4. [Type Distribution Matrix](#4-type-distribution-matrix)")
    w("5. [Exercise Quick-Reference Table](#5-exercise-quick-reference-table)")
    w("6. [Prerequisite Chain Map](#6-prerequisite-chain-map)")
    w("7. [Lecture Reference Index](#7-lecture-reference-index)")
    w()
    w("---")
    w()

    # === 1. Executive Summary ===
    w("## 1. Executive Summary")
    w()
    w("### Overall Counts")
    w()
    w("| Metric | Value |")
    w("|--------|------:|")
    w(f"| Total exercises ({cfg['languages'][0].upper()}) | **{total}** |")
    for lang in cfg["languages"][1:]:
        w(f"| Total exercises ({lang.upper()} twins) | **{total}** |")
    w(f"| Grand total ({langs}) | **{total_both}** |")
    w(f"| Sessions | **{len(cfg['sessions'])}** |")
    w(f"| Languages | **{len(cfg['languages'])}** ({langs}) |")
    w(f"| Exercises per session ({cfg['languages'][0].upper()}) | **{total // len(cfg['sessions'])}** |")

    all_topics = set()
    all_lectrefs = set()
    data_table_count = 0
    software_count = 0
    software_label = cfg.get("software_tool", "software")
    for ex in all_flat:
        all_topics.update(ex.get("topics", []))
        lr = ex.get("lecture_ref", "")
        if lr:
            all_lectrefs.add(lr)
        if ex.get("data_table"):
            data_table_count += 1
        if ex.get("software_code") or ex.get("stata_code"):
            software_count += 1

    w(f"| Unique topics | **{len(all_topics)}** |")
    w(f"| Unique lecture references | **{len(all_lectrefs)}** |")
    w(f"| Exercises with data tables | **{data_table_count}** |")
    w(f"| Exercises with {software_label} code | **{software_count}** |")
    w()

    # Type distribution
    type_counts = Counter(ex["question_type"] for ex in all_flat)
    w("### Question Type Distribution")
    w()
    w("| Type | Count | % | Description |")
    w("|------|------:|--:|-------------|")
    type_desc = {
        "MATH": "Numerical/algebraic computation",
        "CONCEPT": "Conceptual understanding",
        "INTERP": "Interpretation of output/results",
        "CASE": "Applied case study",
        "TF": "True/False with justification",
        "STATA": "Stata code/output analysis",
        "SOFTWARE": f"{cfg.get('software_tool', 'Software')} code/output analysis",
    }
    for t in cfg["exercise_types"]:
        c = type_counts.get(t, 0)
        pct = c / total * 100 if total else 0
        w(f"| {t} | {c} | {pct:.1f}% | {type_desc.get(t, '')} |")
    w(f"| **Total** | **{total}** | **100%** | |")
    w()

    # Difficulty distribution — keys come from the configured
    # difficulty_distribution so non-default labels (FACILE/MOYEN/DIFFICILE,
    # 1/2/3, etc.) render correctly.
    difficulty_keys = list(cfg.get("difficulty_distribution", {}).keys()) or ["EASY", "MED", "HARD"]
    diff_counts = Counter(ex["difficulty"] for ex in all_flat)
    w("### Difficulty Distribution")
    w()
    w("| Difficulty | Count | % |")
    w("|-----------|------:|--:|")
    for d in difficulty_keys:
        c = diff_counts.get(d, 0)
        pct = c / total * 100 if total else 0
        w(f"| {d} | {c} | {pct:.1f}% |")
    w(f"| **Total** | **{total}** | **100%** |")
    w()

    # Top topics
    topic_counter = Counter()
    for ex in all_flat:
        topic_counter.update(ex.get("topics", []))
    w("### Top 20 Topics Across All Sessions")
    w()
    w("| Rank | Topic | Exercise Count |")
    w("|-----:|-------|---------------:|")
    for rank, (topic, count) in enumerate(topic_counter.most_common(20), 1):
        w(f"| {rank} | `{topic}` | {count} |")
    w()
    w("---")
    w()

    # === 2. Per-Session Overview ===
    w("## 2. Per-Session Overview")
    w()

    languages = cfg.get("languages", ["en"])
    primary_lang = languages[0]
    secondary_langs = languages[1:]
    for session in cfg["sessions"]:
        sid = session["id"]
        exs = all_exercises.get(sid, [])
        primary_title = session.get(f"title_{primary_lang}", sid)
        secondary_titles = [
            session.get(f"title_{l}", "") for l in secondary_langs
        ]

        w(f"### {sid}: {primary_title}")
        for st in secondary_titles:
            if st:
                w(f"*{st}*  ")
        w(f"Directory: `{session['dir']}/`")
        w()

        dt_count = sum(1 for ex in exs if ex.get("data_table"))
        sw_count = sum(1 for ex in exs if ex.get("software_code") or ex.get("stata_code"))
        w(f"**{len(exs)} exercises** | {dt_count} with data tables | {sw_count} with {software_label} code")
        w()

        # Type breakdown
        s_types = Counter(ex["question_type"] for ex in exs)
        w("**Type Breakdown**")
        w()
        w("| Type | Count |")
        w("|------|------:|")
        for t in cfg["exercise_types"]:
            w(f"| {t} | {s_types.get(t, 0)} |")
        w()

        # Difficulty
        s_diff = Counter(ex["difficulty"] for ex in exs)
        w("**Difficulty Breakdown**")
        w()
        w("| Difficulty | Count | Visual |")
        w("|-----------|------:|--------|")
        max_d = max(s_diff.values()) if s_diff else 1
        for d in difficulty_keys:
            c = s_diff.get(d, 0)
            bar = "=" * max(1, int(c / max_d * 15))
            w(f"| {d} | {c} | `{bar}` |")
        w()

        # Topics
        s_topics = Counter()
        for ex in exs:
            s_topics.update(ex.get("topics", []))
        w("**Topics**")
        w()
        w("| Topic | Count |")
        w("|-------|------:|")
        for topic, count in s_topics.most_common():
            w(f"| `{topic}` | {count} |")
        w()

        # Keywords
        texts = [ex["question_text"] for ex in exs]
        keywords = extract_keywords(texts, 20)
        kw_str = ", ".join(f"`{word}` ({count})" for word, count in keywords)
        w("**Top Keywords** (from question text)")
        w()
        w(kw_str)
        w()
        w("---")
        w()

    # === 3. Master Topic Index ===
    w("## 3. Master Topic Index")
    w()
    w("| Topic | Sessions (count) | Total |")
    w("|-------|-----------------|------:|")

    topic_by_session = defaultdict(lambda: Counter())
    for session in cfg["sessions"]:
        sid = session["id"]
        for ex in all_exercises.get(sid, []):
            for t in ex.get("topics", []):
                topic_by_session[t][sid] += 1

    for topic in sorted(topic_by_session.keys()):
        session_parts = []
        total_t = 0
        for session in cfg["sessions"]:
            sid = session["id"]
            if sid in topic_by_session[topic]:
                c = topic_by_session[topic][sid]
                session_parts.append(f"{sid}({c})")
                total_t += c
        w(f"| `{topic}` | {', '.join(session_parts)} | {total_t} |")
    w()
    w("---")
    w()

    # === 4. Type Distribution Matrix ===
    w("## 4. Type Distribution Matrix")
    w()
    w("### Type x Session (with difficulty breakdown)")
    w()
    header = "| Type | " + " | ".join(s["id"] for s in cfg["sessions"]) + " | Total |"
    sep = "|------|" + "|".join("------:" for _ in cfg["sessions"]) + "|------:|"
    w(header)
    w(sep)

    for t in cfg["exercise_types"]:
        row = f"| {t} "
        t_total = 0
        for session in cfg["sessions"]:
            sid = session["id"]
            exs = [ex for ex in all_exercises.get(sid, []) if ex["question_type"] == t]
            c = len(exs)
            t_total += c
            diffs = Counter(ex["difficulty"] for ex in exs)
            breakdown = "/".join(str(diffs.get(d, 0)) for d in difficulty_keys)
            row += f"| {c} ({breakdown}) "
        row += f"| {t_total} |"
        w(row)
    w()
    w(f"*Cell format: count ({'/'.join(difficulty_keys)})*")
    w()

    # Difficulty x Session
    w("### Difficulty x Session")
    w()
    header = "| Difficulty | " + " | ".join(s["id"] for s in cfg["sessions"]) + " | Total |"
    w(header)
    w(sep)
    for d in difficulty_keys:
        row = f"| {d} "
        d_total = 0
        for session in cfg["sessions"]:
            sid = session["id"]
            c = sum(1 for ex in all_exercises.get(sid, []) if ex["difficulty"] == d)
            d_total += c
            row += f"| {c} "
        row += f"| {d_total} |"
        w(row)
    w()
    w("---")
    w()

    # === 5. Exercise Quick-Reference Table ===
    w("## 5. Exercise Quick-Reference Table")
    w()
    if secondary_langs:
        w(
            f"*{primary_lang.upper()} exercises only "
            f"({'/'.join(l.upper() for l in secondary_langs)} are translation twins with identical structure)*"
        )
    w()

    for session in cfg["sessions"]:
        sid = session["id"]
        exs = all_exercises.get(sid, [])
        primary_title = session.get(f"title_{primary_lang}", sid)
        w(f"### {sid}: {primary_title}")
        w()

        for t in cfg["exercise_types"]:
            t_exs = [ex for ex in exs if ex["question_type"] == t]
            if not t_exs:
                continue
            w(f"#### {t}")
            w()
            w("| ID | Diff | Topics | Question (first 80 chars) |")
            w("|----|------|--------|---------------------------|")
            for ex in sorted(t_exs, key=lambda e: e["id"]):
                topics = ", ".join(ex.get("topics", [])[:3])
                if len(ex.get("topics", [])) > 3:
                    topics += "..."
                q = ex["question_text"][:80].replace("|", "/").replace("\n", " ")
                if len(ex["question_text"]) > 80:
                    q += "..."
                w(f"| {ex['id']} | {ex['difficulty']} | {topics} | {q} |")
            w()

    w("---")
    w()

    # === 6. Prerequisite Chain Map ===
    w("## 6. Prerequisite Chain Map")
    w()
    prereq_counter = Counter()
    has_prereqs = 0
    no_prereqs = 0
    for ex in all_flat:
        prereqs = ex.get("prerequisites", [])
        if prereqs:
            has_prereqs += 1
            prereq_counter.update(prereqs)
        else:
            no_prereqs += 1

    w(f"- Exercises with prerequisites: **{has_prereqs}**")
    w(f"- Exercises without prerequisites: **{no_prereqs}**")
    w()
    if prereq_counter:
        w("| Prerequisite | Referenced by |")
        w("|-------------|-------------:|")
        for prereq, count in prereq_counter.most_common():
            w(f"| `{prereq}` | {count} |")
    else:
        w("*All exercises have empty prerequisite arrays (self-contained).*")
    w()
    w("---")
    w()

    # === 7. Lecture Reference Index ===
    w("## 7. Lecture Reference Index")
    w()

    lectref_by_session = defaultdict(lambda: Counter())
    for session in cfg["sessions"]:
        sid = session["id"]
        for ex in all_exercises.get(sid, []):
            lr = ex.get("lecture_ref", "")
            if lr:
                lectref_by_session[sid][lr] += 1

    # Separate structured (S#.#) from descriptive refs
    structured = {}
    descriptive = defaultdict(lambda: Counter())
    for sid, refs in lectref_by_session.items():
        for ref, count in refs.items():
            if re.match(r"^S\d+\.\d+", ref):
                structured.setdefault(sid, Counter())[ref] = count
            else:
                descriptive[sid][ref] = count

    if structured:
        w("### Structured References (S#.# format)")
        w()
        w("| Session | Reference | Count |")
        w("|---------|-----------|------:|")
        for sid in sorted(structured.keys()):
            for ref, count in sorted(structured[sid].items()):
                w(f"| {sid} | `{ref}` | {count} |")
        w()

    if descriptive:
        w("### Descriptive References")
        w()
        for session in cfg["sessions"]:
            sid = session["id"]
            if sid not in descriptive:
                continue
            w(f"**{sid}** ({sum(descriptive[sid].values())} exercises)")
            w()
            for ref, count in descriptive[sid].most_common():
                short_ref = ref[:80] + "..." if len(ref) > 80 else ref
                w(f"- `{short_ref}` ({count})")
            w()

    w("---")
    w()

    # Appendix
    w("## Appendix: Session Directory Map")
    w()
    lang_columns = " | ".join(f"{l.upper()} File" for l in languages)
    w(f"| Session | Directory | {lang_columns} |")
    w("|---------|-----------|" + ("---|" * len(languages)))
    for session in cfg["sessions"]:
        sid = session["id"]
        d = session["dir"]
        lang_files = " | ".join(f"`exercises_{l.upper()}.json`" for l in languages)
        w(f"| {sid} | `{d}/` | {lang_files} |")
    w()

    return "\n".join(lines)


def main():
    cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else None)
    out_dir = get_output_dir(cfg)
    out_path = out_dir / "EXERCISE_BANK_CATALOG.md"

    print(f"Generating catalog for {cfg['course_id']}...")
    catalog = generate_catalog(cfg)

    out_path.write_text(catalog + "\n", encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    line_count = catalog.count("\n") + 1
    print(f"  Written to {out_path}")
    print(f"  {size_kb:.1f} KB, {line_count} lines")
    print("Done.")


if __name__ == "__main__":
    main()
