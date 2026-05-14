#!/usr/bin/env python3
"""Unit tests for pipeline/llm_providers.py and audit finding dedupe."""

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import config_loader
import llm_providers
import run
from llm_providers import ProviderConfig, call_llm
from run import Pipeline, _dedupe_findings


def test_provider_config_from_dict_valid():
    cfg = ProviderConfig.from_dict({
        "provider": "claude",
        "model": "claude-opus-4-7",
        "api_key_env": None,
        "extra_args": ["--verbose"],
    })

    assert cfg == ProviderConfig(
        provider="claude",
        model="claude-opus-4-7",
        api_key_env=None,
        extra_args=["--verbose"],
    )


def test_provider_config_from_dict_missing_provider_raises():
    with pytest.raises(ValueError, match="provider"):
        ProviderConfig.from_dict({"model": "claude-opus-4-7"})


def test_provider_config_from_dict_applies_optional_defaults():
    cfg = ProviderConfig.from_dict({"provider": "codex"})

    assert cfg.provider == "codex"
    assert cfg.model is None
    assert cfg.api_key_env is None
    assert cfg.extra_args == []


@pytest.mark.parametrize("provider_name, helper_name", [
    ("claude", "_call_claude"),
    ("codex", "_call_codex"),
])
def test_call_llm_dispatches_to_expected_helper(monkeypatch, provider_name, helper_name):
    calls = []

    def fake_helper(cfg, prompt, system_prompt, timeout, label):
        calls.append((cfg, prompt, system_prompt, timeout, label))
        return f"{provider_name}-ok"

    monkeypatch.setattr(llm_providers, helper_name, fake_helper)

    cfg = ProviderConfig(provider=provider_name, model="model-x")
    result = call_llm(
        cfg,
        "prompt text",
        system_prompt="system text",
        timeout=123,
        label="audit-label",
    )

    assert result == f"{provider_name}-ok"
    assert calls == [(cfg, "prompt text", "system text", 123, "audit-label")]


@pytest.mark.parametrize("provider_name", ["openai", "ollama", "vibe"])
def test_call_llm_unimplemented_provider_raises_helpful_error(provider_name):
    with pytest.raises(NotImplementedError, match=rf"{provider_name}.*pipeline/llm_providers.py"):
        call_llm(ProviderConfig(provider=provider_name), "prompt")


def test_call_claude_builds_expected_argv(monkeypatch):
    calls = {}

    def fake_default_prompt():
        return "DEFAULT SYSTEM"

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="claude-output", stderr="")

    monkeypatch.setattr(llm_providers, "_default_claude_system_prompt", fake_default_prompt)
    monkeypatch.setattr(llm_providers.subprocess, "run", fake_run)

    cfg = ProviderConfig(
        provider="claude",
        model="claude-opus-4-7",
        extra_args=["--foo", "bar"],
    )
    result = llm_providers._call_claude(
        cfg,
        "PROMPT BODY",
        None,
        321,
        "label-a",
    )

    assert result == "claude-output"
    assert calls["cmd"] == [
        "claude",
        "-p",
        "--model",
        "claude-opus-4-7",
        "--append-system-prompt",
        "DEFAULT SYSTEM",
        "--dangerously-skip-permissions",
        "--foo",
        "bar",
    ]
    assert calls["kwargs"]["input"] == "PROMPT BODY"
    assert calls["kwargs"]["capture_output"] is True
    assert calls["kwargs"]["text"] is True
    assert calls["kwargs"]["timeout"] == 321


def test_call_codex_builds_expected_argv(monkeypatch, tmp_path):
    calls = {"cleaned": []}
    output_path = tmp_path / "codex_output.md"

    def fake_clean(path):
        calls["cleaned"].append(path)

    def fake_mkstemp(prefix, suffix):
        fd = os.open(output_path, os.O_CREAT | os.O_RDWR | os.O_TRUNC)
        return fd, str(output_path)

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls["kwargs"] = kwargs
        output_path.write_text("# audit\n", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(llm_providers, "_clean_tmp_dir", fake_clean)
    monkeypatch.setattr(llm_providers.tempfile, "mkstemp", fake_mkstemp)
    monkeypatch.setattr(llm_providers.subprocess, "run", fake_run)

    cfg = ProviderConfig(
        provider="codex",
        model="gpt-5.4",
        extra_args=["-c", "model_reasoning_effort=high"],
    )
    result = llm_providers._call_codex(
        cfg,
        "PROMPT BODY",
        "SYSTEM BODY",
        654,
        "label-b",
    )

    assert result == "# audit\n"
    assert calls["cleaned"] == [Path("/tmp/codex-cache"), Path("/tmp/codex-skills")]
    assert calls["cmd"] == [
        "codex",
        "exec",
        "-m",
        "gpt-5.4",
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
        "-C",
        str(llm_providers._PROJECT_ROOT),
        "-o",
        str(output_path),
        "-c",
        "model_reasoning_effort=high",
        "SYSTEM BODY\n\nPROMPT BODY",
    ]
    assert calls["kwargs"]["capture_output"] is True
    assert calls["kwargs"]["text"] is True
    assert calls["kwargs"]["timeout"] == 654
    assert not output_path.exists()


def test_dedupe_findings_keeps_highest_severity_per_exercise_and_category():
    findings = [
        {
            "exercise_id": "S1_EN_CONCEPT_001",
            "category": "math",
            "severity": "warning",
            "message": "weaker finding",
        },
        {
            "exercise_id": "S1_EN_CONCEPT_001",
            "category": "math",
            "severity": "critical",
            "message": "stronger finding",
        },
        {
            "exercise_id": "S1_EN_CONCEPT_001",
            "category": "format",
            "severity": "minor",
            "message": "different category",
        },
        {
            "exercise_id": "S1_EN_CONCEPT_002",
            "category": "math",
            "severity": "major",
            "message": "different exercise",
        },
    ]

    deduped = _dedupe_findings(findings)
    by_key = {
        (finding["exercise_id"], finding["category"]): finding
        for finding in deduped
    }

    assert len(deduped) == 3
    assert by_key[("S1_EN_CONCEPT_001", "math")]["severity"] == "critical"
    assert by_key[("S1_EN_CONCEPT_001", "math")]["message"] == "stronger finding"
    assert by_key[("S1_EN_CONCEPT_001", "format")]["severity"] == "minor"
    assert by_key[("S1_EN_CONCEPT_002", "math")]["severity"] == "major"


def test_run_audit_pass_uses_codex_specific_prompt(tmp_path, monkeypatch):
    cfg = {
        "course_id": "test_course",
        "languages": ["en", "fr"],
        "sessions": [{
            "id": "S1",
            "dir": "S1",
            "title_en": "S1",
            "title_fr": "S1",
            "topics": ["intro"],
            "exercise_count": 1,
            "type_distribution": {"CONCEPT": 1},
        }],
        "exercise_types": ["CONCEPT"],
        "difficulty_distribution": {"EASY": 1.0},
        "id_regex": r"^.*$",
        "solution_constraints": {"max_words": 100, "hints_min": 2, "hints_max": 3},
        "math_validation": {"checks": []},
        "pipeline": {"max_fix_iterations": 1},
        "llm": {
            "generation": {"provider": "claude"},
            "verifiers": [{"provider": "codex"}],
        },
    }
    cfg_path = tmp_path / "course_config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    calls = {}

    def fake_audit_prompt(self, session_id):
        calls["self_prompt_session"] = session_id
        return "SELF PROMPT"

    def fake_codex_prompt(cfg_obj, session):
        calls["codex_prompt_session"] = session["id"]
        return "CODEX PROMPT"

    def fake_call_llm(verifier, prompt, *, timeout=600, label="", system_prompt=None):
        calls["verifier"] = verifier
        calls["prompt"] = prompt
        calls["timeout"] = timeout
        calls["label"] = label
        return "```findings_json\n[]\n```"

    def fake_save_findings(self, findings, session_id, source="claude"):
        calls["saved"] = (findings, session_id, source)

    monkeypatch.setattr(Pipeline, "audit_prompt", fake_audit_prompt)
    monkeypatch.setattr(run, "render_codex_audit_prompt", fake_codex_prompt)
    monkeypatch.setattr(run, "call_llm", fake_call_llm)
    monkeypatch.setattr(Pipeline, "save_findings", fake_save_findings)

    pipeline = Pipeline(str(cfg_path))
    findings = pipeline.run_audit_pass("S1", ProviderConfig(provider="codex", model="gpt-5.4"), 0)

    assert findings == []
    assert calls["codex_prompt_session"] == "S1"
    assert "self_prompt_session" not in calls
    assert calls["prompt"] == "CODEX PROMPT"
    assert calls["label"] == "S1_audit_round_1"
    assert calls["saved"] == ([], "S1", "codex_round1")


def test_pending_assessment_style_basis_blocks_generation(tmp_path, capsys):
    cfg = {
        "course_id": "test_course",
        "languages": ["en"],
        "assessment_style_basis": "pending_assessment_style_audit",
        "sessions": [{
            "id": "S1",
            "dir": "S1",
            "title_en": "S1",
            "topics": ["intro"],
            "exercise_count": 1,
            "type_distribution": {"CONCEPT": 1},
        }],
        "exercise_types": ["CONCEPT"],
        "difficulty_distribution": {"EASY": 1.0},
        "id_regex": r"^.*$",
        "solution_constraints": {"max_words": 100, "hints_min": 2, "hints_max": 3},
        "math_validation": {"checks": []},
        "pipeline": {"max_fix_iterations": 1},
        "llm": {
            "generation": {"provider": "claude"},
            "verifiers": [{"provider": "claude"}],
        },
    }
    cfg_path = tmp_path / "course_config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    with pytest.raises(SystemExit):
        config_loader.load_config(cfg_path)

    captured = capsys.readouterr()
    assert "pending_assessment_style_audit" in captured.err


def test_pending_nested_exercise_profile_basis_blocks_generation(tmp_path, capsys):
    cfg = {
        "course_id": "test_course",
        "languages": ["en"],
        "exercise_profile": {"basis": "pending_assessment_style_audit"},
        "sessions": [{
            "id": "S1",
            "dir": "S1",
            "title_en": "S1",
            "topics": ["intro"],
            "exercise_count": 1,
            "type_distribution": {"CONCEPT": 1},
        }],
        "exercise_types": ["CONCEPT"],
        "difficulty_distribution": {"EASY": 1.0},
        "id_regex": r"^.*$",
        "solution_constraints": {"max_words": 100, "hints_min": 2, "hints_max": 3},
        "math_validation": {"checks": []},
        "pipeline": {"max_fix_iterations": 1},
        "llm": {
            "generation": {"provider": "claude"},
            "verifiers": [{"provider": "claude"}],
        },
    }
    cfg_path = tmp_path / "course_config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    with pytest.raises(SystemExit):
        config_loader.load_config(cfg_path)

    captured = capsys.readouterr()
    assert "pending_assessment_style_audit" in captured.err
