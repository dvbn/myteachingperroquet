#!/usr/bin/env python3
"""Exercise generation pipeline — helper module.

Steps 1 (generate), 2 (self-audit), 4 (fix) are done by Claude interactively.
Step 3 (independent audit) calls configured LLM verifiers as subprocesses.

This module provides:
  - Prompt rendering wrappers
  - File I/O helpers (save batches, aggregate, apply fixes)
  - Provider-backed audit runner (Step 3)
  - CLI for: dry-run, codex audit, aggregation

Interactive usage (Claude imports this):
    from run import Pipeline
    p = Pipeline()                          # loads config
    p = Pipeline("path/to/config.json")     # custom config

    # Step 1: Generation
    prompt = p.generation_prompt("S1", loop=1)   # render prompt
    p.save_batch(exercises, "S1", loop=1, lang="EN")  # save output
    prompt = p.twin_prompt("S1", loop=1, target_lang="FR")
    p.save_batch(twins, "S1", loop=1, lang="FR")
    p.aggregate("S1")                       # merge batches → exercises_{LANG}.json

    # Step 2: Self-audit
    prompt = p.audit_prompt("S1")           # render audit prompt
    p.save_findings(findings, "S1")         # save findings JSON

    # Step 3: Independent audits
    p.run_all_audits("S1")                  # configured verifier passes
    p.run_codex_audit("S1")                 # deprecated wrapper

    # Step 4: Fix
    exercises_to_fix = p.get_flagged("S1")  # {id: {exercise, findings}}
    prompt = p.fix_prompt(exercise, findings)
    p.apply_fix("S1", exercise_id, fixed_exercise)
    # apply_fix already writes back and recomputes related_exercises per call.
    # For a forward-reference reclassification, use apply_relocation instead:
    # p.apply_relocation(finding)

CLI usage:
    python3 pipeline/run.py --dry-run                    # render all prompts
    python3 pipeline/run.py --sessions S1 --codex        # run Codex audit only
    python3 pipeline/run.py --sessions S1 --aggregate    # aggregate batches only
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config_loader import (
    load_config, get_output_dir, get_session_path, get_scaling_config,
    get_primary_language, get_languages,
)
from llm_providers import ProviderConfig, call_llm
from postprocessor import compute_related, normalize_topics, remap_exercise_ids
from scope_resolver import get_excluded_terms, build_term_pattern, extract_exercise_text
from prompt_renderer import (
    render_full_generation_prompt, render_full_twin_prompt,
    render_self_audit_prompt, render_codex_audit_prompt,
    render_fix_prompt, build_batch_schema,
    get_inbox_content,
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_FINDING_SEVERITY_RANK = {
    "critical": 5,
    "major": 4,
    "warning": 3,
    "minor": 2,
    "suggestion": 1,
}


def _atomic_write_json(path: Path, data) -> None:
    """Write JSON via temp-file + rename, so a crash mid-write cannot leave
    a partially-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def _dedupe_findings(findings: list[dict]) -> list[dict]:
    """Deduplicate findings by (exercise_id, category), keeping highest severity."""
    best_by_key: dict[tuple[str, str], dict] = {}
    key_order: list[tuple[str, str]] = []

    for finding in findings:
        key = (
            str(finding.get("exercise_id", "")),
            str(finding.get("category", "")),
        )
        if key not in best_by_key:
            best_by_key[key] = finding
            key_order.append(key)
            continue

        current = best_by_key[key]
        current_rank = _FINDING_SEVERITY_RANK.get(str(current.get("severity", "")).lower(), 0)
        new_rank = _FINDING_SEVERITY_RANK.get(str(finding.get("severity", "")).lower(), 0)
        if new_rank > current_rank:
            best_by_key[key] = finding

    return [best_by_key[key] for key in key_order]


def _data_table_to_markdown(obj):
    """Convert {headers, rows} object to markdown table string."""
    if not isinstance(obj, dict):
        return obj
    headers = obj.get("headers", [])
    rows = obj.get("rows", [])
    if not headers:
        return None
    lines = []
    lines.append("| " + " | ".join(str(h) if h is not None else "" for h in headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(c) if c is not None else "" for c in row) + " |")
    return "\n".join(lines)


def sanitize_exercises(exercises: list[dict]) -> list[dict]:
    """Sanitize exercises for schema compliance.

    - Convert data_table objects to markdown strings
    - Convert common_mistakes null to empty array
    """
    for ex in exercises:
        if isinstance(ex.get("data_table"), dict):
            ex["data_table"] = _data_table_to_markdown(ex["data_table"])
        sol = ex.get("solution")
        if isinstance(sol, dict) and sol.get("common_mistakes") is None:
            sol["common_mistakes"] = []
    return exercises


class Pipeline:
    """Helper class for the interactive exercise generation pipeline."""

    def __init__(self, config_path: str | None = None):
        self.cfg = load_config(config_path)
        self.primary = get_primary_language(self.cfg)
        self.languages = get_languages(self.cfg)
        self.secondary_langs = [l for l in self.languages if l != self.primary]
        self.batch_size = self.cfg.get("batch_size", 20)
        self.loops = self.cfg.get("generation_loops", 1)

    # ── Step 1: Generation helpers ───────────────────────────────────────

    def generation_prompt(self, session_id: str, loop: int) -> str:
        """Render the generation prompt for a batch (primary language)."""
        session = self._get_session(session_id)
        id_offset = (loop - 1) * self.batch_size + 1
        return render_full_generation_prompt(
            self.cfg, session, self.primary, loop, self.batch_size, id_offset,
        )

    def twin_prompt(self, session_id: str, loop: int, target_lang: str) -> str:
        """Render twin prompt. Reads the primary batch file for source JSON.

        Looks first in the session root, then in the archived `batches/`
        subdirectory (since `aggregate()` moves batch files there once
        merging is done — twins generated AFTER aggregation still work).
        Falls back to slicing the aggregated `exercises_<LANG>.json` for
        the requested loop's worth of exercises if neither batch file
        exists.
        """
        session = self._get_session(session_id)
        batch_path = self._batch_path(session_id, loop, self.primary)
        if not batch_path.exists():
            archived = batch_path.parent / "batches" / batch_path.name
            if archived.exists():
                batch_path = archived
        if batch_path.exists():
            source_json = batch_path.read_text(encoding="utf-8")
        else:
            # Fall back to the aggregated exercises file
            session_path = get_session_path(self.cfg, session_id)
            agg_path = session_path / f"exercises_{self.primary.upper()}.json"
            if not agg_path.exists():
                raise FileNotFoundError(
                    f"No primary-language source for {session_id} "
                    f"(checked {batch_path} and {agg_path})"
                )
            agg = json.loads(agg_path.read_text(encoding="utf-8"))
            start = (loop - 1) * self.batch_size
            slice_ = agg[start:start + self.batch_size]
            source_json = json.dumps(slice_, indent=2, ensure_ascii=False)
        return render_full_twin_prompt(
            self.cfg, session, self.primary, target_lang, source_json,
        )

    def save_batch(self, exercises: list[dict], session_id: str, loop: int, lang: str):
        """Save a batch of exercises to batch_{loop}_{LANG}.json.

        Applies sanitization (data_table format, common_mistakes null→[]) before saving.
        """
        exercises = sanitize_exercises(exercises)
        path = self._batch_path(session_id, loop, lang)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(exercises, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"  Saved {path.name}: {len(exercises)} exercises")

    def aggregate(self, session_id: str):
        """Merge batch files into exercises_{LANG}.json, fill related_exercises,
        then move batch files to a batches/ subdirectory.

        Supports re-runs: if batch files were already archived into batches/,
        reads from there instead.
        """
        session = self._get_session(session_id)
        session_path = get_session_path(self.cfg, session_id)

        for lang in self.languages:
            lang_upper = lang.upper()
            all_exercises = []
            for loop in range(1, self.loops + 1):
                batch_file = self._batch_path(session_id, loop, lang)
                # Fallback to batches/ subdirectory if already archived
                if not batch_file.exists():
                    archived = batch_file.parent / "batches" / batch_file.name
                    if archived.exists():
                        batch_file = archived
                if batch_file.exists():
                    batch = json.loads(batch_file.read_text(encoding="utf-8"))
                    all_exercises.extend(batch)
                else:
                    print(f"  WARNING: Missing {batch_file.name}")

            if not all_exercises:
                print(f"  ERROR: No exercises for {lang_upper}")
                continue

            # Check duplicates
            ids = [ex.get("id", "") for ex in all_exercises]
            dupes = [eid for eid in set(ids) if ids.count(eid) > 1]
            if dupes:
                print(f"  WARNING: Duplicate IDs in {lang_upper}: {dupes[:5]}")

            all_exercises = sanitize_exercises(all_exercises)
            # Apply topic aliases if configured
            alias_map = self.cfg.get("topic_aliases", {})
            if alias_map:
                all_exercises = normalize_topics(all_exercises, alias_map)
            all_exercises = compute_related(all_exercises)
            out_path = session_path / f"exercises_{lang_upper}.json"
            out_path.write_text(
                json.dumps(all_exercises, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(f"  Aggregated: {out_path.name} ({len(all_exercises)} exercises)")

        # Move batch files to batches/ subdirectory to prevent duplicate loading
        self._archive_batches(session_path)

    def _archive_batches(self, session_path: Path):
        """Move batch_*.json and batch_*_prompt.txt into batches/ subdirectory."""
        if not session_path.exists():
            return
        batches_dir = session_path / "batches"
        moved = 0
        for f in session_path.iterdir():
            if f.name.startswith("batch_") and f.suffix in (".json", ".txt"):
                batches_dir.mkdir(exist_ok=True)
                shutil.move(str(f), str(batches_dir / f.name))
                moved += 1
        if moved:
            print(f"  Archived {moved} batch files → batches/")

    def validate_batch(
        self, exercises: list[dict], session_id: str, language: str,
    ) -> list[dict]:
        """Pre-aggregation validation gate.

        Checks:
        1. Exercise topics are in the session's configured topics (with alias resolution)
        2. Exercise text does not reference excluded scope terms

        Returns a list of violation dicts (empty = clean batch).
        """
        session = self._get_session(session_id)
        alias_map = self.cfg.get("topic_aliases", {})

        # Allowed topics: session topics + alias targets
        allowed_topics = set(session.get("topics", []))
        for old, new in alias_map.items():
            if new in allowed_topics:
                allowed_topics.add(old)

        # Excluded terms + patterns
        excluded = get_excluded_terms(self.cfg, session_id, language)
        excluded_pats = [
            (t, build_term_pattern(t)) for t in excluded
        ]

        violations: list[dict] = []

        for ex in exercises:
            eid = ex.get("id", "unknown")

            # Check 1: topic scope
            for topic in ex.get("topics", []):
                if topic not in allowed_topics:
                    violations.append({
                        "exercise_id": eid,
                        "check": "topic_scope",
                        "detail": f"Topic '{topic}' not in session {session_id} topics",
                    })

            # Check 2: excluded term scan
            text = extract_exercise_text(ex)
            if not text.strip():
                continue
            for term, pat in excluded_pats:
                if pat and pat.search(text):
                    violations.append({
                        "exercise_id": eid,
                        "check": "excluded_term",
                        "detail": f"References excluded term '{term}'",
                    })

        return violations

    def relocate_exercises(
        self, id_map: dict[str, str], session_ids: list[str] | None = None,
    ):
        """Apply exercise ID remapping across session files, then recompute related_exercises.

        id_map: {"old_id": "new_id", ...}
        session_ids: limit to these sessions (default: all)
        """
        targets = session_ids or [s["id"] for s in self.cfg["sessions"]]

        for sid in targets:
            session_path = get_session_path(self.cfg, sid)
            for lang in self.languages:
                json_path = session_path / f"exercises_{lang.upper()}.json"
                if not json_path.exists():
                    continue
                exercises = json.loads(json_path.read_text(encoding="utf-8"))
                exercises = remap_exercise_ids(exercises, id_map)
                exercises = compute_related(exercises)
                json_path.write_text(
                    json.dumps(exercises, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                remapped_ids = set(id_map.values())
                remapped_count = sum(
                    1 for ex in exercises if ex.get("id") in remapped_ids
                )
                if remapped_count:
                    print(f"  Relocated {remapped_count} exercise(s) in {json_path.name}")

    def get_schema(self) -> dict:
        """Return the exercise JSON schema."""
        schema_path = get_output_dir(self.cfg) / "schema.json"
        return json.loads(schema_path.read_text(encoding="utf-8"))

    # ── Step 2: Self-audit helpers ───────────────────────────────────────

    def audit_prompt(self, session_id: str) -> str:
        """Render the self-audit prompt with all exercises inlined."""
        session = self._get_session(session_id)
        exercises_json = self._load_exercises_json(session_id)
        return render_self_audit_prompt(self.cfg, session, exercises_json)

    def save_findings(self, findings: list[dict], session_id: str, source: str = "claude"):
        """Save audit findings to validation directory."""
        validation_dir = get_output_dir(self.cfg) / "validation" / f"{source}_audit"
        validation_dir.mkdir(parents=True, exist_ok=True)
        path = validation_dir / f"{source}_audit_{session_id}_findings.json"
        _atomic_write_json(path, findings)
        crit = sum(1 for f in findings if f.get("severity") == "critical")
        print(f"  Saved {len(findings)} findings ({crit} critical) → {path.name}")

    # ── Step 3: Independent audits ───────────────────────────────────────

    def run_audit_pass(
        self, session_id: str, verifier: ProviderConfig, round_index: int,
    ) -> list[dict]:
        """Run one configured audit pass and return parsed findings."""
        scaling = get_scaling_config(self.cfg)
        timeout = scaling.get("subprocess_timeout_secs", 600)
        if verifier.provider == "codex":
            # Preserve the legacy Codex external-audit prompt shape.
            prompt = render_codex_audit_prompt(self.cfg, self._get_session(session_id))
        else:
            prompt = self.audit_prompt(session_id)
        label = f"{session_id}_audit_round_{round_index + 1}"

        print(f"  Running {verifier.provider} audit round {round_index + 1} for {session_id}...")
        raw = call_llm(
            verifier,
            prompt,
            timeout=timeout,
            label=label,
        )
        findings = _parse_findings_json(raw)
        self.save_findings(
            findings,
            session_id,
            source=f"{verifier.provider}_round{round_index + 1}",
        )
        return findings

    def run_all_audits(self, session_id: str) -> list[dict]:
        """Run all configured verifier passes and return deduplicated findings."""
        verifiers = self.cfg.get("llm", {}).get("verifiers", [])
        if not verifiers:
            print(
                f"WARNING: no llm.verifiers configured for {session_id}; skipping independent audits",
                file=sys.stderr,
            )
            return []

        all_findings: list[dict] = []
        for round_index, verifier_cfg in enumerate(verifiers):
            verifier = ProviderConfig.from_dict(verifier_cfg)
            all_findings.extend(self.run_audit_pass(session_id, verifier, round_index))
        return _dedupe_findings(all_findings)

    def run_codex_audit(self, session_id: str) -> list[dict]:
        """Deprecated backward-compat wrapper. Prefer run_all_audits()."""
        scaling = get_scaling_config(self.cfg)
        verifier = ProviderConfig(
            provider="codex",
            model=scaling.get("codex_model", "gpt-5.4"),
        )
        return self.run_audit_pass(session_id, verifier, 0)

    # ── Step 4: Fix helpers ──────────────────────────────────────────────

    def get_flagged(self, session_id: str) -> dict[str, dict]:
        """Load findings and return {exercise_id: {exercise, findings}} for critical/major."""
        validation_dir = get_output_dir(self.cfg) / "validation"
        session_path = get_session_path(self.cfg, session_id)

        # Collect all findings
        all_findings = []
        for audit_path in sorted(validation_dir.glob("*_audit")):
            if not audit_path.is_dir():
                continue
            for f in audit_path.glob(f"*_{session_id}_findings.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        all_findings.extend(data)
                except (json.JSONDecodeError, OSError):
                    pass

        # Group by exercise
        by_exercise: dict[str, list[dict]] = {}
        for f in all_findings:
            eid = f.get("exercise_id", "")
            if eid and f.get("severity") in ("critical", "major"):
                by_exercise.setdefault(eid, []).append(f)

        if not by_exercise:
            return {}

        # Load exercises
        exercises_by_id = {}
        for lang in self.languages:
            json_path = session_path / f"exercises_{lang.upper()}.json"
            if json_path.exists():
                for ex in json.loads(json_path.read_text(encoding="utf-8")):
                    exercises_by_id[ex["id"]] = ex

        result = {}
        for eid, findings in by_exercise.items():
            if eid in exercises_by_id:
                result[eid] = {
                    "exercise": exercises_by_id[eid],
                    "findings": findings,
                }
        return result

    def fix_prompt(self, exercise: dict, findings: list[dict]) -> str:
        """Render a fix prompt for one exercise."""
        ex_json = json.dumps(exercise, indent=2, ensure_ascii=False)
        return render_fix_prompt(self.cfg, ex_json, findings)

    def apply_fix(self, session_id: str, exercise_id: str, fixed_exercise: dict):
        """Replace one exercise in the session files."""
        session_path = get_session_path(self.cfg, session_id)
        for lang in self.languages:
            json_path = session_path / f"exercises_{lang.upper()}.json"
            if not json_path.exists():
                continue
            exercises = json.loads(json_path.read_text(encoding="utf-8"))
            for i, ex in enumerate(exercises):
                if ex["id"] == exercise_id:
                    exercises[i] = fixed_exercise
                    exercises = compute_related(exercises)
                    json_path.write_text(
                        json.dumps(exercises, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                    print(f"  Fixed {exercise_id} in {json_path.name}")
                    return
        print(f"  WARNING: {exercise_id} not found in exercise files")

    def apply_relocation(self, finding: dict) -> tuple[str, str]:
        """Reclassify an exercise (and its twin) to a different session.

        Driven by an audit finding with:
            recommended_action: "reclassify"
            target_session:      "<S_k>"

        Steps:
          1. Find the exercise + its twin in the source session JSON files.
          2. Compute new IDs in the target session, allocating the next free
             trailing number if there is a collision.
          3. Physically move both entries from source to target session files.
          4. Call relocate_exercises({old: new}) to refresh id, twin_id,
             prerequisites, and related_exercises across all session files.

        Returns (new_id, new_twin_id) for caller logging.
        """
        action = finding.get("recommended_action")
        if action != "reclassify":
            raise ValueError(
                f"apply_relocation requires recommended_action='reclassify', "
                f"got '{action}'"
            )

        old_id = finding.get("exercise_id")
        target_session = finding.get("target_session")
        if not old_id or not target_session:
            raise ValueError(
                "apply_relocation requires 'exercise_id' and 'target_session'"
            )

        # Locate the exercise + its twin
        exercise, source_session, source_lang = self._find_exercise(old_id)
        if exercise is None:
            raise ValueError(f"Exercise {old_id} not found in any session")
        twin_old_id = exercise.get("twin_id")
        twin, _, twin_lang = (
            self._find_exercise(twin_old_id) if twin_old_id else (None, None, None)
        )

        # Verify target session exists in config
        self._get_session(target_session)

        # Same-session reclassification is a no-op semantically and an active
        # hazard mechanically (would renumber the exercise in place because the
        # current ID is "occupied"). Reject early.
        if source_session == target_session:
            raise ValueError(
                f"target_session ({target_session}) is the same as the source "
                f"session for {old_id}; reclassification is a no-op"
            )

        # Joint primary+twin number allocation: pick the smallest trailing
        # number that is free in BOTH the EN and the FR target files, so the
        # twin pair stays symmetric.
        new_id, new_twin_id = self._compute_paired_new_ids(
            old_id, twin_old_id, target_session,
        )

        # Build id_map (used both inside _move and for cross-ref refresh)
        id_map = {old_id: new_id}
        if twin_old_id and new_twin_id:
            id_map[twin_old_id] = new_twin_id

        # Atomic move: rename + write target first, then write source.
        # Worst case under crash is a duplicate (entry in target AND source),
        # which is recoverable. Never a drop.
        self._move_exercise_between_sessions(
            old_id, new_id, source_session, target_session, source_lang,
        )
        if twin and twin_old_id and new_twin_id:
            self._move_exercise_between_sessions(
                twin_old_id, new_twin_id, source_session, target_session, twin_lang,
            )

        # Refresh related_exercises and prerequisites pointing at the old
        # IDs in OTHER session files (the moved entry is already final).
        self.relocate_exercises(id_map)

        print(f"  Reclassified {old_id} → {new_id} (and twin {twin_old_id} → {new_twin_id})")
        return new_id, new_twin_id

    # ── Internals ────────────────────────────────────────────────────────

    def _find_exercise(self, exercise_id: str) -> tuple[dict | None, str | None, str | None]:
        """Search all session files for an exercise. Returns (ex, session_id, lang)."""
        if not exercise_id:
            return None, None, None
        for sess in self.cfg["sessions"]:
            sid = sess["id"]
            session_path = get_session_path(self.cfg, sid)
            for lang in self.languages:
                json_path = session_path / f"exercises_{lang.upper()}.json"
                if not json_path.exists():
                    continue
                exercises = json.loads(json_path.read_text(encoding="utf-8"))
                for ex in exercises:
                    if ex.get("id") == exercise_id:
                        return ex, sid, lang
        return None, None, None

    def _parse_id_parts(self, eid: str) -> tuple[str, str, str, str]:
        """Return (session, lang_token, type_token, number) parts of an exercise ID.

        Assumes shape {SESSION}_{LANG}_{TYPE}_{NNN}.
        """
        parts = eid.split("_")
        if len(parts) < 4:
            raise ValueError(f"Cannot parse exercise ID: {eid}")
        return parts[0], parts[1], parts[-2], parts[-1]

    def _existing_numbers_in_target(
        self, target_session: str, lang_token: str, type_token: str,
    ) -> set[int]:
        """Return the set of trailing numbers already used by exercises matching
        {target_session}_{lang_token}_{type_token}_NNN in the target session's
        JSON file. Returns an empty set if the file does not exist.
        """
        target_path = (
            get_session_path(self.cfg, target_session) / f"exercises_{lang_token}.json"
        )
        if not target_path.exists():
            return set()
        prefix = f"{target_session}_{lang_token}_{type_token}_"
        used: set[int] = set()
        for ex in json.loads(target_path.read_text(encoding="utf-8")):
            eid = ex.get("id", "")
            if eid.startswith(prefix):
                tail = eid[len(prefix):]
                if tail.isdigit():
                    used.add(int(tail))
        return used

    def _compute_paired_new_ids(
        self, primary_id: str, twin_id: str | None, target_session: str,
    ) -> tuple[str, str | None]:
        """Allocate matching trailing numbers for a primary/twin pair in
        the target session.

        Picks the smallest trailing number that is free in BOTH the primary
        language file and the twin language file. Falls back to the primary's
        original number if it is jointly free.

        Raises RuntimeError if no free number exists within the original
        ID width (e.g. 1..999 for 3-digit IDs).
        """
        _, p_lang, p_type, p_num = self._parse_id_parts(primary_id)
        width = len(p_num)
        max_n = (10 ** width) - 1  # e.g. 999 for width=3

        primary_used = self._existing_numbers_in_target(target_session, p_lang, p_type)

        if twin_id:
            _, t_lang, t_type, t_num = self._parse_id_parts(twin_id)
            if len(t_num) != width or t_type != p_type:
                # Twin should mirror primary on type and width; if not, the
                # spec's "same number on its side" guarantee no longer applies.
                raise ValueError(
                    f"Twin {twin_id} does not mirror primary {primary_id} "
                    "(different type or width)"
                )
            twin_used = self._existing_numbers_in_target(target_session, t_lang, t_type)
        else:
            t_lang = None
            twin_used = set()

        joint_used = primary_used | twin_used
        candidate = int(p_num)
        if candidate not in joint_used:
            chosen = candidate
        else:
            chosen = None
            for n in range(1, max_n + 1):
                if n not in joint_used:
                    chosen = n
                    break
            if chosen is None:
                raise RuntimeError(
                    f"No free {width}-digit number for {p_type} in {target_session}"
                )

        new_primary = f"{target_session}_{p_lang}_{p_type}_{chosen:0{width}d}"
        new_twin = (
            f"{target_session}_{t_lang}_{p_type}_{chosen:0{width}d}"
            if twin_id else None
        )
        return new_primary, new_twin

    def _move_exercise_between_sessions(
        self,
        old_id: str,
        new_id: str,
        source_session: str,
        target_session: str,
        language: str,
    ):
        """Move an exercise from source session JSON to target session JSON,
        renaming and updating session-scoped metadata in a single atomic pass.

        The moved entry's `id` is set to `new_id`, `session` is set to the
        target session, `session_title_<lang>` fields are reset to the
        target session's titles, and `lecture_ref` is cleared to a
        placeholder (the source value is a per-session slide pointer that
        is meaningless in the target session).

        Atomicity: target is written FIRST (with the entry in its final
        renamed form), then source is written without the entry. Worst case
        under crash is a duplicate (entry visible in both files); never a
        drop. Both writes use `_atomic_write_json` (temp + rename).
        """
        if source_session == target_session:
            return  # Defense in depth; apply_relocation rejects earlier.

        lang_upper = language.upper()
        source_path = get_session_path(self.cfg, source_session) / f"exercises_{lang_upper}.json"
        target_path = get_session_path(self.cfg, target_session) / f"exercises_{lang_upper}.json"

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        source_exercises = json.loads(source_path.read_text(encoding="utf-8"))
        moved = None
        remaining = []
        for ex in source_exercises:
            if ex.get("id") == old_id:
                moved = ex
            else:
                remaining.append(ex)
        if moved is None:
            raise ValueError(f"{old_id} not in {source_path}")

        # Final-state metadata: rename id and flip all session-scoped fields
        target_session_obj = self._get_session(target_session)
        moved["id"] = new_id
        # twin_id will be patched by the caller's relocate_exercises pass
        # after both halves of the pair have moved (since the twin's new id
        # is only known here for the side currently being moved).
        moved["session"] = target_session
        for lang in self.languages:
            title_key = f"session_title_{lang}"
            if title_key in moved:
                moved[title_key] = target_session_obj.get(f"title_{lang}", target_session)
        if "lecture_ref" in moved:
            moved["lecture_ref"] = f"{target_session}.?"

        # Write target FIRST (final state)
        target_exercises = []
        if target_path.exists():
            target_exercises = json.loads(target_path.read_text(encoding="utf-8"))
        target_exercises.append(moved)
        _atomic_write_json(target_path, target_exercises)

        # Then write source minus moved
        _atomic_write_json(source_path, remaining)

    def _get_session(self, session_id: str) -> dict:
        session = next((s for s in self.cfg["sessions"] if s["id"] == session_id), None)
        if not session:
            raise ValueError(f"Session {session_id} not found in config")
        return session

    def _batch_path(self, session_id: str, loop: int, lang: str) -> Path:
        return get_session_path(self.cfg, session_id) / f"batch_{loop}_{lang.upper()}.json"

    def _load_exercises_json(self, session_id: str) -> str:
        session_path = get_session_path(self.cfg, session_id)
        all_data = {}
        for lang in self.languages:
            json_path = session_path / f"exercises_{lang.upper()}.json"
            if json_path.exists():
                all_data[lang.upper()] = json.loads(json_path.read_text(encoding="utf-8"))
        return json.dumps(all_data, indent=2, ensure_ascii=False) if all_data else ""

    def session_info(self, session_id: str) -> str:
        """Print session status summary."""
        session = self._get_session(session_id)
        session_path = get_session_path(self.cfg, session_id)
        lines = [
            f"Session {session_id}: {session.get('title_en', '')}",
            f"  Batch size: {self.batch_size}, Loops: {self.loops}, "
            f"Total target: {self.batch_size * self.loops}",
            f"  Languages: {', '.join(self.languages)} (primary: {self.primary})",
            f"  Types: {session.get('type_distribution', {})}",
        ]
        # Check existing files
        for lang in self.languages:
            for loop in range(1, self.loops + 1):
                bp = self._batch_path(session_id, loop, lang)
                if bp.exists():
                    n = len(json.loads(bp.read_text(encoding="utf-8")))
                    lines.append(f"  {bp.name}: {n} exercises")
            agg = session_path / f"exercises_{lang.upper()}.json"
            if agg.exists():
                n = len(json.loads(agg.read_text(encoding="utf-8")))
                lines.append(f"  {agg.name}: {n} exercises (aggregated)")
        return "\n".join(lines)


# ── Utility functions ────────────────────────────────────────────────────

def parse_json_output(raw: str) -> list[dict] | None:
    """Extract a JSON array from text. Handles fenced blocks."""
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("["):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    m = re.search(r"```(?:json)?\s*\n(\[[\s\S]*?\])\s*\n```", raw)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    start = raw.find("[")
    end = raw.rfind("]")
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None


def _parse_findings_json(raw: str) -> list[dict]:
    """Extract findings_json block from audit output."""
    if not raw:
        return []
    m = re.search(r"```findings_json\s*\n(\[[\s\S]*?\])\s*\n```", raw)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return []


# ── CLI (for dry-run, codex, aggregation) ────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Pipeline helper CLI")
    p.add_argument("--config", default=None)
    p.add_argument("--sessions", default=None, help="Comma-separated session IDs")
    p.add_argument("--dry-run", action="store_true", help="Render and save all prompts")
    p.add_argument("--codex", action="store_true", help="Run Codex audit only")
    p.add_argument("--aggregate", action="store_true", help="Aggregate batches only")
    p.add_argument("--info", action="store_true", help="Show session status")
    args = p.parse_args()

    pipe = Pipeline(args.config)

    session_ids = (
        [s.strip() for s in args.sessions.split(",")]
        if args.sessions
        else [s["id"] for s in pipe.cfg["sessions"]]
    )

    for sid in session_ids:
        if args.info:
            print(pipe.session_info(sid))
            print()
            continue

        if args.aggregate:
            print(f"Aggregating {sid}...")
            pipe.aggregate(sid)
            continue

        if args.codex:
            pipe.run_codex_audit(sid)
            continue

        if args.dry_run:
            session = pipe._get_session(sid)
            session_path = get_session_path(pipe.cfg, sid)
            session_path.mkdir(parents=True, exist_ok=True)

            print(f"\nSession {sid}: {session.get('title_en', '')}")

            # Step 1 prompts
            for loop in range(1, pipe.loops + 1):
                prompt = pipe.generation_prompt(sid, loop)
                path = session_path / f"batch_{loop}_{pipe.primary.upper()}_prompt.txt"
                path.write_text(prompt, encoding="utf-8")
                print(f"  [dry-run] {path.name} ({len(prompt)} chars)")

                for tl in pipe.secondary_langs:
                    # Twin prompt needs source exercises (use placeholder in dry-run)
                    twin_prompt = render_full_twin_prompt(
                        pipe.cfg, session, pipe.primary, tl, "[]",
                    )
                    tp = session_path / f"batch_{loop}_{tl.upper()}_prompt.txt"
                    tp.write_text(twin_prompt, encoding="utf-8")
                    print(f"  [dry-run] {tp.name} ({len(twin_prompt)} chars)")

            print("  Done.\n")


if __name__ == "__main__":
    main()
