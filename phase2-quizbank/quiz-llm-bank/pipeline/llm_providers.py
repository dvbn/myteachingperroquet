#!/usr/bin/env python3
"""LLM provider dispatch for pipeline subprocess calls."""

import ast
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_RUN_EXPERIMENT_PATH = _PROJECT_ROOT / "scripts" / "experiments" / "run_experiment.py"


@dataclass
class ProviderConfig:
    provider: str
    model: str | None = None
    api_key_env: str | None = None
    extra_args: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderConfig":
        """Validate a provider config dict and return a dataclass instance."""
        if not isinstance(data, dict):
            raise ValueError("Provider config must be a dict")

        provider = data.get("provider")
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("Provider config requires a non-empty 'provider' string")

        model = data.get("model")
        if model is not None and not isinstance(model, str):
            raise ValueError("'model' must be a string or null")

        api_key_env = data.get("api_key_env")
        if api_key_env is not None and not isinstance(api_key_env, str):
            raise ValueError("'api_key_env' must be a string or null")

        extra_args = data.get("extra_args", [])
        if extra_args is None:
            extra_args = []
        if not isinstance(extra_args, list) or any(not isinstance(arg, str) for arg in extra_args):
            raise ValueError("'extra_args' must be a list of strings")

        return cls(
            provider=provider,
            model=model,
            api_key_env=api_key_env,
            extra_args=list(extra_args),
        )


def call_llm(
    cfg: ProviderConfig,
    prompt: str,
    *,
    system_prompt: str | None = None,
    timeout: int = 600,
    label: str = "",
) -> str:
    """Call the configured LLM and return its raw stdout/markdown output."""
    if cfg.provider == "claude":
        return _call_claude(cfg, prompt, system_prompt, timeout, label)
    if cfg.provider == "codex":
        return _call_codex(cfg, prompt, system_prompt, timeout, label)
    if cfg.provider == "openai":
        return _call_openai(cfg, prompt, system_prompt, timeout, label)
    if cfg.provider == "ollama":
        return _call_ollama(cfg, prompt, system_prompt, timeout, label)
    if cfg.provider == "vibe":
        return _call_vibe(cfg, prompt, system_prompt, timeout, label)
    raise ValueError(f"Unknown provider: {cfg.provider!r}")


@lru_cache(maxsize=1)
def _default_claude_system_prompt() -> str:
    """Load the audit execution-mode prompt from scripts/experiments/run_experiment.py."""
    source = _RUN_EXPERIMENT_PATH.read_text(encoding="utf-8")
    string_group = r'(?:"(?:[^"\\]|\\.)*"\s*)+'
    pattern = (
        r"def run_claude_text\(.*?"
        r'"--append-system-prompt",\s*'
        rf"({string_group})"
    )
    match = re.search(pattern, source, re.DOTALL)
    if not match:
        raise RuntimeError(
            f"Could not load Claude execution-mode prompt from {_RUN_EXPERIMENT_PATH}"
        )
    value = ast.literal_eval(f"({match.group(1)})")
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            f"Claude execution-mode prompt in {_RUN_EXPERIMENT_PATH} is empty or invalid"
        )
    return value


def _clean_tmp_dir(path: Path) -> None:
    if not path.exists():
        return
    for child in path.iterdir():
        try:
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        except OSError:
            pass


def _subprocess_env(cfg: ProviderConfig) -> dict[str, str]:
    """Return the subprocess environment, preserving any provider auth vars."""
    env = os.environ.copy()
    if cfg.api_key_env and cfg.api_key_env not in env:
        raise RuntimeError(
            f"Provider '{cfg.provider}' expects env var {cfg.api_key_env!r}, but it is not set"
        )
    return env


def _call_claude(
    cfg: ProviderConfig,
    prompt: str,
    system_prompt: str | None,
    timeout: int,
    label: str,
) -> str:
    if system_prompt is None:
        system_prompt = _default_claude_system_prompt()

    cmd = [
        "claude",
        "-p",
        "--model",
        cfg.model or "claude-opus-4-7",
        "--append-system-prompt",
        system_prompt,
        "--dangerously-skip-permissions",
        *cfg.extra_args,
    ]
    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_subprocess_env(cfg),
    )
    if result.returncode != 0:
        target = label or "claude call"
        raise RuntimeError(
            f"{target} failed with exit {result.returncode}: {result.stderr.strip()[:500]}"
        )
    return result.stdout


def _call_codex(
    cfg: ProviderConfig,
    prompt: str,
    system_prompt: str | None,
    timeout: int,
    label: str,
) -> str:
    _clean_tmp_dir(Path("/tmp/codex-cache"))
    _clean_tmp_dir(Path("/tmp/codex-skills"))

    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    fd, tmp_path = tempfile.mkstemp(
        prefix=f"{label or 'codex'}_",
        suffix=".md",
    )
    os.close(fd)
    output_path = Path(tmp_path)

    cmd = [
        "codex",
        "exec",
        "-m",
        cfg.model or "gpt-5.4",
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
        "-C",
        str(_PROJECT_ROOT),
        "-o",
        str(output_path),
        *cfg.extra_args,
        full_prompt,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_subprocess_env(cfg),
        )
        if result.returncode != 0:
            target = label or "codex call"
            raise RuntimeError(
                f"{target} failed with exit {result.returncode}: {result.stderr.strip()[:500]}"
            )
        if not output_path.exists():
            raise RuntimeError(f"Codex call did not produce output file: {output_path}")
        return output_path.read_text(encoding="utf-8")
    finally:
        try:
            output_path.unlink()
        except OSError:
            pass


def _call_openai(
    cfg: ProviderConfig,
    prompt: str,
    system_prompt: str | None,
    timeout: int,
    label: str,
) -> str:
    raise NotImplementedError(
        "Provider 'openai' is recognized but not yet implemented. "
        "Add _call_openai() in pipeline/llm_providers.py."
    )


def _call_ollama(
    cfg: ProviderConfig,
    prompt: str,
    system_prompt: str | None,
    timeout: int,
    label: str,
) -> str:
    raise NotImplementedError(
        "Provider 'ollama' is recognized but not yet implemented. "
        "Add _call_ollama() in pipeline/llm_providers.py."
    )


def _call_vibe(
    cfg: ProviderConfig,
    prompt: str,
    system_prompt: str | None,
    timeout: int,
    label: str,
) -> str:
    raise NotImplementedError(
        "Provider 'vibe' is recognized but not yet implemented. "
        "Add _call_vibe() in pipeline/llm_providers.py."
    )
