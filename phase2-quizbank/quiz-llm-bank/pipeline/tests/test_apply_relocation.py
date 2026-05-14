#!/usr/bin/env python3
"""Unit tests for Pipeline.apply_relocation.

Covers:
- Reclassifying an exercise + twin to a target session
- ID collision handling (next-free trailing number)
- Cross-reference updates (related_exercises, prerequisites)
- Twin parity preservation
- Error paths (missing target_session, wrong recommended_action)

Run: python3 -m pytest pipeline/tests/test_apply_relocation.py -v
"""

import json
import sys
from pathlib import Path

# Make pipeline modules importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import config_loader
from run import Pipeline


# ── Fixtures ────────────────────────────────────────────────────────────────


def _make_session(sid: str, dir_name: str | None = None) -> dict:
    return {
        "id": sid,
        "dir": dir_name or sid,
        "title_en": f"{sid} title EN",
        "title_fr": f"{sid} title FR",
        "topics": [f"{sid}_topic"],
        "exercise_count": 2,
        "type_distribution": {"MATH": 2},
        "prerequisites": [],
    }


def _make_cfg(course_id: str = "test_course") -> dict:
    return {
        "course_id": course_id,
        "languages": ["en", "fr"],
        "sessions": [_make_session("S1"), _make_session("S2")],
        "exercise_types": ["MATH"],
        "difficulty_distribution": {"EASY": 0.5, "MED": 0.5},
        "id_regex": r"^S\d+_(EN|FR)_[A-Z]+_\d{3}$",
        "solution_constraints": {"max_words": 300, "hints_min": 2, "hints_max": 3},
        "math_validation": {"checks": []},
        "pipeline": {"max_fix_iterations": 3},
    }


def _make_exercise(eid: str, twin_id: str, session: str, lang: str) -> dict:
    return {
        "id": eid,
        "twin_id": twin_id,
        "session": session,
        "session_title_en": f"{session} title EN",
        "session_title_fr": f"{session} title FR",
        "language": lang,
        "question_type": "MATH",
        "difficulty": "MED",
        "topics": [f"{session}_topic"],
        "prerequisites": [],
        "lecture_ref": f"{session}.1",
        "question_text": f"Question for {eid}",
        "solution": {"text": "Solution.", "key_formula": None},
        "hints": ["Hint 1", "Hint 2"],
        "related_exercises": [],
    }


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    """Set up a synthetic repo with config + S1/S2 directories + exercise JSONs."""
    cfg = _make_cfg()
    course_id = cfg["course_id"]

    # Write config
    cfg_path = tmp_path / "course_config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    # Output dirs
    out_dir = tmp_path / "output" / course_id
    s1_dir = out_dir / "S1"
    s2_dir = out_dir / "S2"
    s1_dir.mkdir(parents=True)
    s2_dir.mkdir(parents=True)

    # S1: 2 exercises (EN + FR twins)
    s1_en = [
        _make_exercise("S1_EN_MATH_001", "S1_FR_MATH_001", "S1", "en"),
        _make_exercise("S1_EN_MATH_002", "S1_FR_MATH_002", "S1", "en"),
    ]
    s1_fr = [
        _make_exercise("S1_FR_MATH_001", "S1_EN_MATH_001", "S1", "fr"),
        _make_exercise("S1_FR_MATH_002", "S1_EN_MATH_002", "S1", "fr"),
    ]
    # Add a related_exercises link from 002 → 001 to test cross-ref update
    s1_en[1]["related_exercises"] = ["S1_EN_MATH_001"]
    s1_fr[1]["related_exercises"] = ["S1_FR_MATH_001"]

    (s1_dir / "exercises_EN.json").write_text(
        json.dumps(s1_en, indent=2) + "\n", encoding="utf-8"
    )
    (s1_dir / "exercises_FR.json").write_text(
        json.dumps(s1_fr, indent=2) + "\n", encoding="utf-8"
    )

    # S2: empty (will receive moved exercises)
    (s2_dir / "exercises_EN.json").write_text("[]\n", encoding="utf-8")
    (s2_dir / "exercises_FR.json").write_text("[]\n", encoding="utf-8")

    # Redirect output dir resolution to tmp_path
    monkeypatch.setattr(config_loader, "get_output_dir", lambda cfg: out_dir)
    # run.py imports get_output_dir directly, so patch there too
    import run
    monkeypatch.setattr(run, "get_output_dir", lambda cfg: out_dir)
    # And get_session_path uses get_output_dir internally — patch run's reference
    monkeypatch.setattr(
        run,
        "get_session_path",
        lambda cfg, sid: out_dir / next(s["dir"] for s in cfg["sessions"] if s["id"] == sid),
    )

    return {
        "tmp_path": tmp_path,
        "cfg_path": cfg_path,
        "out_dir": out_dir,
        "s1_dir": s1_dir,
        "s2_dir": s2_dir,
    }


def _read_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


# ── Tests ───────────────────────────────────────────────────────────────────


def test_reclassify_moves_exercise_and_twin(tmp_repo):
    """Reclassifying S1_EN_MATH_001 → S2 moves both EN exercise and FR twin."""
    p = Pipeline(tmp_repo["cfg_path"])
    finding = {
        "exercise_id": "S1_EN_MATH_001",
        "recommended_action": "reclassify",
        "target_session": "S2",
        "category": "forward_reference",
    }

    new_id, new_twin_id = p.apply_relocation(finding)

    assert new_id == "S2_EN_MATH_001"
    assert new_twin_id == "S2_FR_MATH_001"

    # S1 lost the exercise + twin
    s1_en = _read_json(tmp_repo["s1_dir"] / "exercises_EN.json")
    s1_fr = _read_json(tmp_repo["s1_dir"] / "exercises_FR.json")
    s1_en_ids = {ex["id"] for ex in s1_en}
    s1_fr_ids = {ex["id"] for ex in s1_fr}
    assert "S1_EN_MATH_001" not in s1_en_ids
    assert "S1_FR_MATH_001" not in s1_fr_ids
    assert "S1_EN_MATH_002" in s1_en_ids  # untouched

    # S2 gained them with renamed IDs
    s2_en = _read_json(tmp_repo["s2_dir"] / "exercises_EN.json")
    s2_fr = _read_json(tmp_repo["s2_dir"] / "exercises_FR.json")
    s2_en_by_id = {ex["id"]: ex for ex in s2_en}
    s2_fr_by_id = {ex["id"]: ex for ex in s2_fr}
    assert "S2_EN_MATH_001" in s2_en_by_id
    assert "S2_FR_MATH_001" in s2_fr_by_id

    # Twin pointers updated symmetrically
    assert s2_en_by_id["S2_EN_MATH_001"]["twin_id"] == "S2_FR_MATH_001"
    assert s2_fr_by_id["S2_FR_MATH_001"]["twin_id"] == "S2_EN_MATH_001"


def test_reclassify_updates_related_exercises_in_source(tmp_repo):
    """A related_exercises link in S1 pointing at the moved exercise gets updated."""
    p = Pipeline(tmp_repo["cfg_path"])
    p.apply_relocation({
        "exercise_id": "S1_EN_MATH_001",
        "recommended_action": "reclassify",
        "target_session": "S2",
    })

    # S1_EN_MATH_002 originally had related_exercises=["S1_EN_MATH_001"]
    s1_en = _read_json(tmp_repo["s1_dir"] / "exercises_EN.json")
    ex_002 = next(ex for ex in s1_en if ex["id"] == "S1_EN_MATH_002")
    # After relocate, the link is either removed (compute_related runs and finds
    # no overlap) or updated to the new ID. Either way, "S1_EN_MATH_001" must
    # NOT remain — that ID no longer exists.
    assert "S1_EN_MATH_001" not in ex_002["related_exercises"]


def test_reclassify_collision_allocates_next_free_number(tmp_repo):
    """If S2 already has _001, the moved exercise gets the next free number."""
    # Pre-populate S2 with an EN/FR pair using number 001
    pre_s2_en = [_make_exercise("S2_EN_MATH_001", "S2_FR_MATH_001", "S2", "en")]
    pre_s2_fr = [_make_exercise("S2_FR_MATH_001", "S2_EN_MATH_001", "S2", "fr")]
    (tmp_repo["s2_dir"] / "exercises_EN.json").write_text(
        json.dumps(pre_s2_en, indent=2) + "\n", encoding="utf-8"
    )
    (tmp_repo["s2_dir"] / "exercises_FR.json").write_text(
        json.dumps(pre_s2_fr, indent=2) + "\n", encoding="utf-8"
    )

    p = Pipeline(tmp_repo["cfg_path"])
    new_id, new_twin_id = p.apply_relocation({
        "exercise_id": "S1_EN_MATH_001",
        "recommended_action": "reclassify",
        "target_session": "S2",
    })

    assert new_id == "S2_EN_MATH_002"
    assert new_twin_id == "S2_FR_MATH_002"

    # The pre-existing S2_EN_MATH_001 is still there
    s2_en_ids = {ex["id"] for ex in _read_json(tmp_repo["s2_dir"] / "exercises_EN.json")}
    assert "S2_EN_MATH_001" in s2_en_ids
    assert "S2_EN_MATH_002" in s2_en_ids


def test_reclassify_rejects_wrong_action(tmp_repo):
    """apply_relocation rejects findings with non-reclassify recommended_action."""
    p = Pipeline(tmp_repo["cfg_path"])
    with pytest.raises(ValueError, match="reclassify"):
        p.apply_relocation({
            "exercise_id": "S1_EN_MATH_001",
            "recommended_action": "rewrite",
            "target_session": "S2",
        })


def test_reclassify_rejects_missing_target(tmp_repo):
    """apply_relocation requires target_session."""
    p = Pipeline(tmp_repo["cfg_path"])
    with pytest.raises(ValueError, match="target_session"):
        p.apply_relocation({
            "exercise_id": "S1_EN_MATH_001",
            "recommended_action": "reclassify",
        })


def test_reclassify_rejects_unknown_target(tmp_repo):
    """apply_relocation fails fast if target_session is not in config."""
    p = Pipeline(tmp_repo["cfg_path"])
    with pytest.raises(ValueError, match="not found"):
        p.apply_relocation({
            "exercise_id": "S1_EN_MATH_001",
            "recommended_action": "reclassify",
            "target_session": "S99",
        })


def test_reclassify_missing_exercise_raises(tmp_repo):
    """apply_relocation raises if the exercise_id doesn't exist in any session."""
    p = Pipeline(tmp_repo["cfg_path"])
    with pytest.raises(ValueError, match="not found"):
        p.apply_relocation({
            "exercise_id": "S1_EN_MATH_999",
            "recommended_action": "reclassify",
            "target_session": "S2",
        })


# ── Regression tests for codex audit findings ───────────────────────────────


def test_reclassify_updates_session_metadata(tmp_repo):
    """The moved entry must carry the target session in `session` and
    target session titles in `session_title_*`. Stale source-session
    metadata would trip structural validation."""
    p = Pipeline(tmp_repo["cfg_path"])
    p.apply_relocation({
        "exercise_id": "S1_EN_MATH_001",
        "recommended_action": "reclassify",
        "target_session": "S2",
    })
    s2_en = _read_json(tmp_repo["s2_dir"] / "exercises_EN.json")
    moved = next(ex for ex in s2_en if ex["id"] == "S2_EN_MATH_001")
    assert moved["session"] == "S2"
    assert moved["session_title_en"] == "S2 title EN"
    assert moved["session_title_fr"] == "S2 title FR"
    # lecture_ref should be reset (it was a per-session pointer)
    assert moved["lecture_ref"].startswith("S2.")
    assert moved["lecture_ref"] != "S1.1"


def test_paired_collision_keeps_pair_symmetric(tmp_repo):
    """If S2_EN already has _001 but S2_FR does not, the moved exercise
    must still pick a number free in BOTH files so the pair stays symmetric.
    """
    pre_s2_en = [_make_exercise("S2_EN_MATH_001", "S2_FR_MATH_001", "S2", "en")]
    (tmp_repo["s2_dir"] / "exercises_EN.json").write_text(
        json.dumps(pre_s2_en, indent=2) + "\n", encoding="utf-8"
    )
    # Note: S2_FR is left empty — _001 is free on the FR side
    p = Pipeline(tmp_repo["cfg_path"])
    new_id, new_twin_id = p.apply_relocation({
        "exercise_id": "S1_EN_MATH_001",
        "recommended_action": "reclassify",
        "target_session": "S2",
    })
    # Both the EN and the FR twin must end on the SAME trailing number
    assert new_id.split("_")[-1] == new_twin_id.split("_")[-1]
    # And it must not be 001 (taken in EN)
    assert new_id == "S2_EN_MATH_002"
    assert new_twin_id == "S2_FR_MATH_002"


def test_reclassify_rejects_same_session(tmp_repo):
    """target_session == source_session is a no-op semantically and a
    hazard mechanically; must be rejected, not silently renumbered."""
    p = Pipeline(tmp_repo["cfg_path"])
    with pytest.raises(ValueError, match="same as the source"):
        p.apply_relocation({
            "exercise_id": "S1_EN_MATH_001",
            "recommended_action": "reclassify",
            "target_session": "S1",
        })


def test_paired_allocation_overflow_raises(tmp_repo, monkeypatch):
    """If the target session has no free 3-digit number, allocation must
    raise — not silently produce a 4-digit ID that violates the schema regex.
    """
    p = Pipeline(tmp_repo["cfg_path"])
    # Stub the existing-numbers helper to claim every number is taken
    monkeypatch.setattr(
        p, "_existing_numbers_in_target",
        lambda *args, **kwargs: set(range(1, 1000)),
    )
    with pytest.raises(RuntimeError, match="No free"):
        p.apply_relocation({
            "exercise_id": "S1_EN_MATH_001",
            "recommended_action": "reclassify",
            "target_session": "S2",
        })


def test_atomic_move_target_written_first(tmp_repo, monkeypatch):
    """If the move crashes between writing target and writing source, the
    target should already have the entry — worst case is a duplicate, never
    a drop. We simulate by failing the source write and confirming the
    target file still has the moved entry."""
    p = Pipeline(tmp_repo["cfg_path"])

    real_atomic_write = None
    import run as run_module
    real_atomic_write = run_module._atomic_write_json

    call_count = {"n": 0}
    source_path = tmp_repo["s1_dir"] / "exercises_EN.json"

    def maybe_fail(path, data):
        call_count["n"] += 1
        # Fail on the SOURCE write (which happens AFTER target per fix)
        if path == source_path:
            raise IOError("simulated crash mid-source-write")
        real_atomic_write(path, data)

    monkeypatch.setattr(run_module, "_atomic_write_json", maybe_fail)

    with pytest.raises(IOError):
        p.apply_relocation({
            "exercise_id": "S1_EN_MATH_001",
            "recommended_action": "reclassify",
            "target_session": "S2",
        })

    # Target must already contain the moved entry (atomicity guarantee)
    s2_en = _read_json(tmp_repo["s2_dir"] / "exercises_EN.json")
    assert any(ex["id"] == "S2_EN_MATH_001" for ex in s2_en)
