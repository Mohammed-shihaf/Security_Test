"""
Whitebox tests — IAC-001: Open Firewall Rule Detection
======================================================
Metric:  IAC-001  |  L5: Open Firewall Rule Count
Formula: Firewall_Risk = Count(Open_Ports)*30 + Count(Wildcard_CIDRs)*15
Score:   MAX(0, 100 − Firewall_Risk)
Checks:  CKV_AWS_25 (SSH/22 from 0.0.0.0/0)  |  CKV_AWS_24 (RDP/3389 from 0.0.0.0/0)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from normalize_metrics import iac_001  # noqa: E402 — scripts/ added above

from tests.helpers import (
    compliance_score,
    failed_ids,
    passed_ids,
    print_check_summary,
    COMPLIANT_DIR,
    VIOLATION_FILES,
    run_checkov,
)

# Checkov check IDs that cover IAC-001 (CIS Benchmark 4.1 / 4.2)
SSH_CHECK = "CKV_AWS_24"   # Ingress 0.0.0.0/0 → port 22
RDP_CHECK = "CKV_AWS_25"   # Ingress 0.0.0.0/0 → port 3389
OPEN_FW_CHECKS = {SSH_CHECK, RDP_CHECK}

pytestmark = pytest.mark.iac001


class TestOpenFirewallRuleDetection:
    """Verify that open ingress rules on non-web ports are correctly flagged."""

    def test_ssh_port_open_to_world_is_detected(self, checkov_open_firewall):
        """
        open_security_group.tf exposes SSH (port 22) to 0.0.0.0/0.
        Checkov MUST report CKV_AWS_25 as failed.
        """
        fails = failed_ids(checkov_open_firewall)
        print("\nFailed checks on open_security_group.tf:")
        print_check_summary(checkov_open_firewall, "violation")

        assert SSH_CHECK in fails, (
            f"CKV_AWS_25 not found in failed checks — "
            f"scanner may not have fired.\nFailed: {sorted(fails)}"
        )

    def test_violation_fixture_produces_failures(self, checkov_open_firewall):
        """The violation fixture must generate at least one failed check."""
        fails = failed_ids(checkov_open_firewall)
        assert fails, "Checkov found zero violations — scanner may not be working"

    def test_compliant_fixture_has_no_ssh_violation(self, checkov_compliant):
        """
        minimal.tf allows only HTTP (80) and HTTPS (443) from the internet.
        CKV_AWS_25 must NOT be in failed checks.
        """
        fails = failed_ids(checkov_compliant)
        ssh_violations = OPEN_FW_CHECKS & fails
        print(f"\nOpen-firewall checks in compliant dir: {ssh_violations or 'none'}")

        assert not ssh_violations, (
            f"Compliant fixture incorrectly fails firewall checks: {ssh_violations}"
        )

    def test_iac001_score_for_violation_fixture(self, checkov_open_firewall):
        """
        IAC-001 score must be < 100 when SSH is exposed to the internet.
        Score formula: MAX(0, 100 − (open_ports*30 + wildcard_cidrs*15))
        """
        fails = failed_ids(checkov_open_firewall)
        open_ports = 1 if SSH_CHECK in fails else 0
        wildcard_cidrs = open_ports  # one SG with one wildcard CIDR

        result = iac_001(open_ports, wildcard_cidrs)
        print(f"\nIAC-001 score (violation fixture): {result}")

        assert result["normalized_0_100"] < 100, (
            "Score should be <100 when open firewall rules are present"
        )
        assert result["raw"]["Firewall_Risk"] > 0

    def test_iac001_score_for_compliant_fixture(self, checkov_compliant):
        """IAC-001 score must be 100 when no sensitive ports are exposed."""
        fails = failed_ids(checkov_compliant)
        open_ports = len(OPEN_FW_CHECKS & fails)
        wildcard_cidrs = open_ports

        result = iac_001(open_ports, wildcard_cidrs)
        print(f"\nIAC-001 score (compliant fixture): {result}")

        assert result["normalized_0_100"] == 100.0, (
            "Score should be 100 when no open firewall rules are present"
        )

    def test_compliant_pass_rate_exceeds_violation(
        self, checkov_open_firewall, checkov_compliant
    ):
        """
        Compliant fixture overall Checkov pass-rate must be higher than
        the violation fixture for the same set of checks.
        """
        _, _, viol_pct = compliance_score(checkov_open_firewall)
        _, _, comp_pct = compliance_score(checkov_compliant)
        print(
            f"\nPass rate — violation fixture: {viol_pct:.1f}%  "
            f"compliant fixture: {comp_pct:.1f}%"
        )
        assert comp_pct >= viol_pct, (
            "Expected compliant fixture to have a higher (or equal) pass rate "
            f"than violation fixture; got {comp_pct:.1f}% vs {viol_pct:.1f}%"
        )
