#!/usr/bin/env python3
"""Re-run codex audits for S1, S2, S3 with the fixed subprocess flags.
Cleans /tmp/codex-cache before each call per global CLAUDE.md."""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from run import Pipeline  # noqa: E402


def clean_codex_cache():
    for p in [Path("/tmp/codex-cache"), Path("/tmp/codex-skills")]:
        if p.exists():
            for child in p.iterdir():
                try:
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                except OSError:
                    pass


def main():
    p = Pipeline()
    for sid in ["S1", "S2", "S3"]:
        print(f"\n=== Codex audit {sid} ===", flush=True)
        clean_codex_cache()
        p.run_codex_audit(sid)


if __name__ == "__main__":
    main()
