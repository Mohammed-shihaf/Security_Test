#!/usr/bin/env python3
"""
Apply L5 normalization formulas from metrics/registry.yaml to raw counts / rates.

Usage:
  python scripts/normalize_metrics.py --secrets-count 2
  python scripts/normalize_metrics.py --secrets-count 1 --sec001-pass-min 50
  python scripts/normalize_metrics.py --demo-sec001-lab-split --json
  python scripts/normalize_metrics.py --historical-secrets 1 --open-sg 1 --public-buckets 1 --unencrypted 1
  python scripts/normalize_metrics.py --cis-pass 48 --cis-total 50
  python scripts/normalize_metrics.py --bypass-rate-percent 5 --overprivileged 2
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any


def clamp_0_100(x: float) -> float:
    return max(0.0, min(100.0, x))


def sec_001(secrets_count: int, pass_min_normalized: float | None = None) -> dict[str, Any]:
    score = max(0.0, 100.0 - (secrets_count * 50))
    out: dict[str, Any] = {
        "metric": "SEC-001 Secrets Exposed in Code Count",
        "raw": {"Secrets_Count": secrets_count},
        "normalized_0_100": score,
        "gate_strict_org_policy": "BLOCK if Secrets_Count > 0 (typical production)",
    }
    if pass_min_normalized is not None:
        out["lab_floor_normalized_pct"] = pass_min_normalized
        out["pass_at_lab_floor"] = score >= pass_min_normalized
    return out


def demo_sec001_lab_split(pass_floor: float = 50.0) -> dict[str, Any]:
    """Two fixed scenarios vs a normalized score floor: one passes, one fails (50/50 split)."""
    scenarios = (("clean_repo", 0), ("two_distinct_findings", 2))
    metrics: list[dict[str, Any]] = []
    for name, count in scenarios:
        score = max(0.0, 100.0 - (count * 50))
        metrics.append(
            {
                "scenario": name,
                "Secrets_Count": count,
                "normalized_0_100": score,
                "pass_at_lab_floor_pct": score >= pass_floor,
            }
        )
    passed_n = sum(1 for m in metrics if m["pass_at_lab_floor_pct"])
    return {
        "lab_note": "Versus a normalized score floor (default 50): clean repo passes; "
        "two findings score 0 and fail — lab pass rate across these scenarios is 50%.",
        "pass_floor_normalized": pass_floor,
        "metrics": metrics,
        "lab_pass_rate_across_scenarios": passed_n / len(metrics),
    }


def sec_003(historical_secrets: int) -> dict[str, Any]:
    historical_exposure_score = historical_secrets * 40
    score = max(0.0, 100.0 - historical_exposure_score)
    return {
        "metric": "SEC-003 Historical Secret Exposure Count",
        "raw": {
            "Historical_Secrets": historical_secrets,
            "Historical_Exposure_Score": historical_exposure_score,
        },
        "normalized_0_100": score,
        "expected": "Historical_Secrets == 0",
    }


def iac_001(open_ports: int, wildcard_cidrs: int) -> dict[str, Any]:
    firewall_risk = open_ports * 30 + wildcard_cidrs * 15
    score = max(0.0, 100.0 - firewall_risk)
    return {
        "metric": "IAC-001 Open Firewall Rule Count",
        "raw": {
            "Open_Ports": open_ports,
            "Wildcard_CIDRs": wildcard_cidrs,
            "Firewall_Risk": firewall_risk,
        },
        "normalized_0_100": score,
    }


def iac_002(unencrypted_resources: int) -> dict[str, Any]:
    deficit = unencrypted_resources * 25
    score = max(0.0, 100.0 - deficit)
    return {
        "metric": "IAC-002 Unencrypted Storage Count",
        "raw": {
            "Unencrypted_Resources": unencrypted_resources,
            "Encryption_Deficit_Score": deficit,
        },
        "normalized_0_100": score,
    }


def iac_003(public_buckets: int) -> dict[str, Any]:
    exposure = public_buckets * 40
    score = max(0.0, 100.0 - exposure)
    return {
        "metric": "IAC-003 Public Storage Bucket Count",
        "raw": {"Public_Buckets": public_buckets, "Public_Exposure_Score": exposure},
        "normalized_0_100": score,
    }


def iac_004(cis_pass: int, cis_total: int, gate: float = 95.0) -> dict[str, Any]:
    if cis_total <= 0:
        raise ValueError("cis_total must be > 0")
    compliance_pct = (cis_pass / cis_total) * 100.0
    return {
        "metric": "IAC-004 CIS Benchmark Compliance",
        "raw": {
            "Passing": cis_pass,
            "Total": cis_total,
            "CIS_Compliance_Pct": round(compliance_pct, 3),
        },
        "normalized_0_100": clamp_0_100(compliance_pct),
        "gate_percent": gate,
        "pass_gate": compliance_pct >= gate,
    }


def sec_002(blocked: int, slipped: int) -> dict[str, Any]:
    denom = blocked + slipped
    block_rate = 100.0 if denom == 0 else (blocked / denom) * 100.0
    return {
        "metric": "SEC-002 Pre-Commit Secret Prevention",
        "raw": {"Blocked": blocked, "Slipped_Through": slipped, "Block_Rate_Pct": block_rate},
        "normalized_0_100": clamp_0_100(block_rate),
        "pass_gate": math.isclose(block_rate, 100.0) and slipped == 0,
    }


def soc_001(bypass_rate_percent: float) -> dict[str, Any]:
    score = max(0.0, 100.0 - (bypass_rate_percent * 20))
    return {
        "metric": "SOC-001 Change Control Verification",
        "raw": {"Bypass_Rate_Pct": bypass_rate_percent},
        "normalized_0_100": score,
        "expected": "Bypass_Rate_Pct == 0",
    }


def soc_002(overprivileged: int) -> dict[str, Any]:
    privilege_score = overprivileged * 20
    score = max(0.0, 100.0 - privilege_score)
    return {
        "metric": "SOC-002 Overprivileged Account Count",
        "raw": {
            "Overprivileged_Accounts": overprivileged,
            "Privilege_Score": privilege_score,
        },
        "normalized_0_100": score,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Normalize whitebox security metrics (0–100).")
    p.add_argument("--secrets-count", type=int, default=None)
    p.add_argument(
        "--sec001-pass-min",
        type=float,
        default=None,
        metavar="PCT",
        help="Lab-only: also emit pass_at_lab_floor if normalized SEC-001 score >= PCT (e.g. 50).",
    )
    p.add_argument(
        "--demo-sec001-lab-split",
        action="store_true",
        help="Print clean vs two-finding scenarios; exactly half pass a 50%% score floor by default.",
    )
    p.add_argument("--historical-secrets", type=int, default=None)
    p.add_argument("--open-sg", type=int, default=0, help="Open sensitive ports count (non-80/443)")
    p.add_argument("--wildcard-cidr", type=int, default=0)
    p.add_argument("--unencrypted", type=int, default=0)
    p.add_argument("--public-buckets", type=int, default=0)
    p.add_argument("--cis-pass", type=int, default=None)
    p.add_argument("--cis-total", type=int, default=None)
    p.add_argument("--blocked-commits", type=int, default=None)
    p.add_argument("--slipped-commits", type=int, default=None)
    p.add_argument("--bypass-rate-percent", type=float, default=None)
    p.add_argument("--overprivileged", type=int, default=None)
    p.add_argument("--json", action="store_true", help="Print single JSON object")

    args = p.parse_args()

    if args.demo_sec001_lab_split:
        floor = 50.0 if args.sec001_pass_min is None else args.sec001_pass_min
        payload = demo_sec001_lab_split(floor)
        print(json.dumps(payload, indent=2))
        return 0

    results: list[dict[str, Any]] = []

    if args.secrets_count is not None:
        results.append(sec_001(args.secrets_count, args.sec001_pass_min))
    if args.historical_secrets is not None:
        results.append(sec_003(args.historical_secrets))
    if args.open_sg or args.wildcard_cidr:
        results.append(iac_001(args.open_sg, args.wildcard_cidr))
    if args.unencrypted:
        results.append(iac_002(args.unencrypted))
    if args.public_buckets:
        results.append(iac_003(args.public_buckets))
    if args.cis_pass is not None and args.cis_total is not None:
        results.append(iac_004(args.cis_pass, args.cis_total))
    if args.blocked_commits is not None and args.slipped_commits is not None:
        results.append(sec_002(args.blocked_commits, args.slipped_commits))
    if args.bypass_rate_percent is not None:
        results.append(soc_001(args.bypass_rate_percent))
    if args.overprivileged is not None:
        results.append(soc_002(args.overprivileged))

    if not results:
        p.print_help()
        return 1

    if args.json:
        print(json.dumps({"metrics": results}, indent=2))
        return 0

    for r in results:
        print(json.dumps(r, indent=2))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
