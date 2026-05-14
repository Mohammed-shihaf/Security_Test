"""
Whitebox tests — IAC-004: CIS Benchmark Compliance
===================================================
Metric:  IAC-004  |  L5: CIS Benchmark Violation Count
Formula: CIS_Compliance_Pct = (Passing / Total) * 100
Score:   CIS_Compliance_Pct  (gate at 95 %)
Tool:    Checkov — all CKV_AWS_* checks against both IaC trees

Strategy
--------
CIS AWS Foundations Benchmark checks are embedded within Checkov's standard
CKV_AWS_* ruleset.  Rather than filtering to a subset, we run the full
terraform framework scan and treat the overall pass-rate as a proxy for
CIS compliance posture — consistent with IAC-004 in metrics/registry.yaml.

The tests assert:
  1. The violation fixtures fail known CIS-mapped checks.
  2. The compliant fixture passes those same checks.
  3. The compliant dir's overall score is higher than the violations dir.
  4. Key individual CIS checks are verified for each fixture.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from normalize_metrics import iac_004  # noqa: E402

from tests.helpers import (
    compliance_score,
    failed_ids,
    passed_ids,
    print_check_summary,
    COMPLIANT_DIR,
    VIOLATIONS_DIR,
    run_checkov,
)

# CIS AWS Foundations — checks we can deterministically verify in our fixtures
CIS_SSH_CHECK = "CKV_AWS_24"     # CIS 4.2  — no ingress port 22 from 0.0.0.0/0
CIS_RDP_CHECK = "CKV_AWS_25"     # CIS 4.1  — no ingress port 3389 from 0.0.0.0/0
CIS_S3_BLOCK_CHECKS = {
    "CKV_AWS_53",                 # block_public_acls
    "CKV_AWS_54",                 # block_public_policy
    "CKV_AWS_55",                 # ignore_public_acls
    "CKV_AWS_56",                 # restrict_public_buckets
}
CIS_RDS_ENCRYPTION = "CKV_AWS_16"   # RDS storage encrypted at rest
CIS_S3_ENCRYPTION = "CKV_AWS_19"    # S3 server-side encryption

ALL_CIS_SPOT_CHECKS = {
    CIS_SSH_CHECK,
    CIS_RDP_CHECK,
    CIS_RDS_ENCRYPTION,
    CIS_S3_ENCRYPTION,
} | CIS_S3_BLOCK_CHECKS

pytestmark = pytest.mark.iac004


class TestCISBenchmarkViolationFixtures:
    """CIS checks must FAIL on known-bad infrastructure definitions."""

    def test_open_ssh_violates_cis_4_2(self, checkov_all_violations):
        """CIS 4.2: No security group should allow unrestricted ingress on port 22."""
        fails = failed_ids(checkov_all_violations)
        assert CIS_SSH_CHECK in fails, (
            f"CIS 4.2 check {CIS_SSH_CHECK} not triggered on violation fixtures.\n"
            f"Failed: {sorted(fails)}"
        )

    def test_unencrypted_rds_violates_cis(self, checkov_all_violations):
        """CIS: RDS instances must have encryption-at-rest enabled."""
        fails = failed_ids(checkov_all_violations)
        assert CIS_RDS_ENCRYPTION in fails, (
            f"CIS RDS encryption check {CIS_RDS_ENCRYPTION} not triggered.\n"
            f"Failed: {sorted(fails)}"
        )

    def test_public_s3_violates_cis(self, checkov_all_violations):
        """CIS: S3 buckets must have public-access block enabled."""
        fails = failed_ids(checkov_all_violations)
        triggered = CIS_S3_BLOCK_CHECKS & fails
        assert triggered, (
            f"No CIS S3 public-access block checks triggered.\n"
            f"Expected any of {CIS_S3_BLOCK_CHECKS}\nFailed: {sorted(fails)}"
        )

    def test_violations_dir_cis_score(self, checkov_all_violations):
        """Report and gate IAC-004 score for the violations directory."""
        passed, total, pct = compliance_score(checkov_all_violations)
        print(f"\nViolations dir — passed: {passed}/{total}  ({pct:.1f}%)")

        result = iac_004(passed, max(total, 1))
        print(f"IAC-004 score (violations): {result}")

        # Violations dir must NOT pass the 95 % CIS gate
        assert not result["pass_gate"], (
            f"Violations directory unexpectedly passed 95% CIS gate: {pct:.1f}%"
        )


class TestCISBenchmarkCompliantFixtures:
    """CIS checks must PASS on the compliant reference IaC."""

    def test_compliant_no_ssh_violation(self, checkov_compliant):
        """CIS 4.2: Compliant fixture must not expose port 22 to 0.0.0.0/0."""
        fails = failed_ids(checkov_compliant)
        assert CIS_SSH_CHECK not in fails, (
            "Compliant fixture incorrectly fails CIS 4.2 SSH check"
        )

    def test_compliant_s3_encryption_passes_cis(self, checkov_compliant):
        """CIS: Compliant S3 bucket must have server-side encryption configured."""
        fails = failed_ids(checkov_compliant)
        assert CIS_S3_ENCRYPTION not in fails, (
            "Compliant S3 fixture fails CIS encryption check CKV_AWS_19"
        )

    def test_compliant_s3_public_access_blocked(self, checkov_compliant):
        """CIS: All four public-access block settings must be true in compliant dir."""
        fails = failed_ids(checkov_compliant)
        public_violations = CIS_S3_BLOCK_CHECKS & fails
        assert not public_violations, (
            f"Compliant fixture fails CIS public-access block checks: "
            f"{public_violations}"
        )

    def test_compliant_dir_higher_cis_score_than_violations(
        self, checkov_compliant, checkov_all_violations
    ):
        """
        Compliant dir's overall Checkov pass-rate must exceed the violations dir.
        This validates that the benchmark fixtures meaningfully differ from the
        compliant baseline.
        """
        _, _, comp_pct = compliance_score(checkov_compliant)
        _, _, viol_pct = compliance_score(checkov_all_violations)

        print(
            f"\nCIS pass-rate — compliant: {comp_pct:.1f}%  "
            f"violations: {viol_pct:.1f}%"
        )
        assert comp_pct > viol_pct, (
            f"Expected compliant ({comp_pct:.1f}%) > violations ({viol_pct:.1f}%)"
        )

    def test_compliant_dir_cis_score_report(self, checkov_compliant):
        """Report IAC-004 score for the compliant directory (informational)."""
        passed, total, pct = compliance_score(checkov_compliant)
        print(f"\nCompliant dir — passed: {passed}/{total}  ({pct:.1f}%)")
        print_check_summary(checkov_compliant, "compliant")

        result = iac_004(passed, max(total, 1))
        print(f"IAC-004 score (compliant): {result}")

        # The compliant fixture is minimal — it may not hit 95 % because it
        # omits optional hardening (logging, replication, CMK, etc.).
        # We only assert that we got a valid score object back.
        assert 0 <= result["normalized_0_100"] <= 100
        assert result["raw"]["CIS_Compliance_Pct"] == round(pct, 3)


class TestCISBenchmarkSummary:
    """Aggregate IAC-004 summary across both trees."""

    def test_spot_check_coverage(self, checkov_all_violations):
        """
        Confirm scanner coverage: all spot-check IDs must appear in *either*
        passed or failed lists (i.e. Checkov evaluated them).
        """
        all_evaluated = (
            failed_ids(checkov_all_violations)
            | passed_ids(checkov_all_violations)
        )
        missing = ALL_CIS_SPOT_CHECKS - all_evaluated
        # CIS_RDP_CHECK may be absent if no SG with port 3389 is defined — skip it
        missing.discard(CIS_RDP_CHECK)

        assert not missing, (
            f"These CIS spot-check IDs were not evaluated by Checkov: {missing}\n"
            "Check that the fixture files are valid Terraform."
        )

    def test_full_iac_cis_report(self, checkov_all_violations, checkov_compliant):
        """Print a side-by-side CIS posture summary (always passes)."""
        vp, vt, vpct = compliance_score(checkov_all_violations)
        cp, ct, cpct = compliance_score(checkov_compliant)

        print("\n" + "=" * 60)
        print("IAC-004  CIS Benchmark — Whitebox Posture Summary")
        print("=" * 60)
        print(f"  Violations dir:  {vp:3d}/{vt:3d} checks passed  ({vpct:6.1f}%)")
        print(f"  Compliant dir:   {cp:3d}/{ct:3d} checks passed  ({cpct:6.1f}%)")

        v_result = iac_004(vp, max(vt, 1))
        c_result = iac_004(cp, max(ct, 1))
        print(f"\n  Score (violations dir):  {v_result['normalized_0_100']:.1f}/100  "
              f"gate={'PASS' if v_result['pass_gate'] else 'FAIL'}")
        print(f"  Score (compliant dir):   {c_result['normalized_0_100']:.1f}/100  "
              f"gate={'PASS' if c_result['pass_gate'] else 'FAIL'}")
        print("=" * 60)

        # This test is purely informational — always passes
        assert True
