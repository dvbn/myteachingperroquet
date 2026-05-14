#!/usr/bin/env python3
"""Structured findings collector for Phase 2 validators."""

import json
from datetime import datetime, timezone


class FindingCollector:
    """Collect structured findings from validators and write to JSON."""

    def __init__(self, source: str):
        self.source = source
        self.findings: list[dict] = []

    def add(
        self,
        severity: str,
        category: str,
        exercise_id: str,
        message: str,
        *,
        evidence: str = "",
        blocking: bool = False,
        recommended_fix: str = "",
        session_id: str = "",
    ):
        finding = {
            "severity": severity,
            "category": category,
            "exercise_id": exercise_id,
            "message": message,
            "source": self.source,
        }
        if evidence:
            finding["evidence"] = evidence
        if blocking:
            finding["blocking"] = True
        if recommended_fix:
            finding["recommended_fix"] = recommended_fix
        if session_id:
            finding["session_id"] = session_id
        self.findings.append(finding)

    def write(self, path: str):
        payload = {
            "source": self.source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_findings": len(self.findings),
            "findings": self.findings,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
