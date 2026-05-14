"""
Shared helper functions for whitebox IaC security tests.

Import this module from test files; the session-scoped fixtures that call
these helpers live in conftest.py (auto-loaded by pytest).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _checkov_cmd() -> list[str]:
    """Return the command prefix needed to invoke checkov on this platform.

    Checkov installs as a console-script stub. On Windows the Scripts/ stub
    is not directly executable; we locate the script file and invoke it
    explicitly via the current Python interpreter.
    """
    # Prefer the sibling Scripts/ entry next to the running interpreter
    scripts_dir = Path(sys.executable).parent / "Scripts"
    for name in ("checkov", "checkov.cmd"):
        candidate = scripts_dir / name
        if candidate.exists():
            return [sys.executable, str(scripts_dir / "checkov")]

    # Fall back to PATH lookup
    found = shutil.which("checkov")
    if found:
        return [sys.executable, found]

    raise FileNotFoundError(
        "checkov not found. Install it with: pip install checkov"
    )

REPO_ROOT = Path(__file__).resolve().parent.parent
VIOLATIONS_DIR = REPO_ROOT / "benchmarks" / "iac" / "violations"
COMPLIANT_DIR = REPO_ROOT / "iac" / "compliant"

VIOLATION_FILES: dict[str, Path] = {
    "open_firewall": VIOLATIONS_DIR / "open_security_group.tf",
    "unencrypted_storage": VIOLATIONS_DIR / "unencrypted_rds.tf",
    "public_storage": VIOLATIONS_DIR / "public_s3.tf",
}


# ---------------------------------------------------------------------------
# Checkov runner
# ---------------------------------------------------------------------------

def run_checkov(
    path: Path,
    check_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Run ``checkov`` against *path* and return the parsed result dict.

    Returns a normalised structure::

        {
            "results": {
                "passed_checks": [...],
                "failed_checks": [...],
                "skipped_checks": [...],
                "parsing_errors": [...],
            }
        }

    Checkov exits with code 1 when violations are found; the return code is
    intentionally ignored.  Timeout is 180 s to prevent CI hangs.
    """
    cmd = _checkov_cmd() + [
        "-d" if path.is_dir() else "-f", str(path),
        "--framework", "terraform",
        "-o", "json",
        "--compact",
        "--quiet",
    ]
    if check_ids:
        cmd += ["--check", ",".join(check_ids)]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=180,
    )

    output = proc.stdout.strip()
    if not output:
        return _empty_result()

    # Strip any leading non-JSON lines checkov sometimes emits on stdout
    json_start = output.find("{")
    array_start = output.find("[")
    if json_start == -1 and array_start == -1:
        return _empty_result()

    if array_start != -1 and (json_start == -1 or array_start < json_start):
        raw = json.loads(output[array_start:])
    else:
        raw = json.loads(output[json_start:])

    if isinstance(raw, list):
        return _merge_list(raw)
    return raw


def _empty_result() -> dict[str, Any]:
    return {
        "results": {
            "passed_checks": [],
            "failed_checks": [],
            "skipped_checks": [],
            "parsing_errors": [],
        }
    }


def _merge_list(items: list[dict]) -> dict[str, Any]:
    merged: dict[str, list] = {
        "passed_checks": [],
        "failed_checks": [],
        "skipped_checks": [],
        "parsing_errors": [],
    }
    for item in items:
        r = item.get("results", {})
        for key in merged:
            merged[key].extend(r.get(key, []))
    return {"results": merged}


# ---------------------------------------------------------------------------
# Convenience accessors
# ---------------------------------------------------------------------------

def failed_ids(result: dict) -> set[str]:
    return {c["check_id"] for c in result["results"]["failed_checks"]}


def passed_ids(result: dict) -> set[str]:
    return {c["check_id"] for c in result["results"]["passed_checks"]}


def compliance_score(result: dict) -> tuple[int, int, float]:
    """Return *(passed, total, pass_pct)*."""
    passed = len(result["results"]["passed_checks"])
    failed = len(result["results"]["failed_checks"])
    total = passed + failed
    pct = (passed / total * 100.0) if total > 0 else 0.0
    return passed, total, round(pct, 2)


def print_check_summary(result: dict, label: str = "") -> None:
    prefix = f"[{label}] " if label else ""
    for c in result["results"]["failed_checks"]:
        print(f"  {prefix}FAIL  {c['check_id']:20s}  {c.get('check_name', '')}")
    for c in result["results"]["passed_checks"]:
        print(f"  {prefix}PASS  {c['check_id']:20s}  {c.get('check_name', '')}")
