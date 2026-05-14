"""
Whitebox tests — IAC-003: Public Storage Access Detection
==========================================================
Metric:  IAC-003  |  L5: Public Storage Bucket Count
Formula: Public_Exposure_Score = Count(Public_Buckets)*40
Score:   MAX(0, 100 − Public_Exposure_Score)
Checks:
  CKV_AWS_53  block_public_acls       = false
  CKV_AWS_54  block_public_policy     = false
  CKV_AWS_55  ignore_public_acls      = false
  CKV_AWS_56  restrict_public_buckets = false
  CKV2_AWS_6  S3 bucket-level Public Access Block
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from normalize_metrics import iac_003  # noqa: E402

from tests.helpers import (
    compliance_score,
    failed_ids,
    passed_ids,
    print_check_summary,
    COMPLIANT_DIR,
    VIOLATION_FILES,
)

# Checkov checks for public-access block settings
PUBLIC_BLOCK_CHECKS = {
    "CKV_AWS_53",   # block_public_acls
    "CKV_AWS_54",   # block_public_policy
    "CKV_AWS_55",   # ignore_public_acls
    "CKV_AWS_56",   # restrict_public_buckets
}
BUCKET_LEVEL_CHECK = "CKV2_AWS_6"

pytestmark = pytest.mark.iac003


class TestPublicStorageAccessDetection:
    """Verify that publicly accessible S3 buckets are correctly flagged."""

    def test_public_access_block_disabled_is_detected(self, checkov_public_storage):
        """
        public_s3.tf sets all four block_public_* flags to false.
        At least one of the PUBLIC_BLOCK_CHECKS must be in failed checks.
        """
        fails = failed_ids(checkov_public_storage)
        print("\nFailed checks on public_s3.tf:")
        print_check_summary(checkov_public_storage, "violation")

        triggered = PUBLIC_BLOCK_CHECKS & fails
        assert triggered, (
            f"None of {PUBLIC_BLOCK_CHECKS} found in failed checks.\n"
            f"Failed: {sorted(fails)}"
        )

    def test_all_four_public_access_block_flags_detected(self, checkov_public_storage):
        """
        Each of the four aws_s3_bucket_public_access_block booleans is false.
        All four dedicated Checkov checks should fire.
        """
        fails = failed_ids(checkov_public_storage)
        missing = PUBLIC_BLOCK_CHECKS - fails
        print(f"\nPublic-block checks triggered: {PUBLIC_BLOCK_CHECKS & fails}")
        print(f"Public-block checks NOT triggered: {missing}")

        assert not missing, (
            f"Expected all four public-block checks to fail; "
            f"missing violations for: {missing}"
        )

    def test_violation_fixture_produces_failures(self, checkov_public_storage):
        """The violation fixture must generate at least one failed check."""
        fails = failed_ids(checkov_public_storage)
        assert fails, "Checkov found zero violations on public_s3.tf"

    def test_compliant_public_access_is_blocked(self, checkov_compliant):
        """
        minimal.tf sets all four block_public_* flags to true.
        None of PUBLIC_BLOCK_CHECKS may be in failed checks.
        """
        fails = failed_ids(checkov_compliant)
        public_violations = PUBLIC_BLOCK_CHECKS & fails
        print(
            f"\nPublic-access block violations in compliant dir: "
            f"{public_violations or 'none'}"
        )

        assert not public_violations, (
            f"Compliant fixture unexpectedly fails public-access block checks: "
            f"{public_violations}"
        )

    def test_iac003_score_for_violation_fixture(self, checkov_public_storage):
        """
        IAC-003 score must be < 100 when public access block is disabled.
        Score formula: MAX(0, 100 − Count(Public_Buckets)*40)
        """
        fails = failed_ids(checkov_public_storage)
        public_buckets = 1 if PUBLIC_BLOCK_CHECKS & fails else 0

        result = iac_003(public_buckets)
        print(f"\nIAC-003 score (violation fixture): {result}")

        assert result["normalized_0_100"] < 100, (
            "Score should be <100 when publicly accessible buckets are present"
        )
        assert result["raw"]["Public_Exposure_Score"] > 0

    def test_iac003_score_for_compliant_fixture(self, checkov_compliant):
        """IAC-003 score must be 100 when no public buckets are detected."""
        fails = failed_ids(checkov_compliant)
        public_buckets = 1 if PUBLIC_BLOCK_CHECKS & fails else 0

        result = iac_003(public_buckets)
        print(f"\nIAC-003 score (compliant fixture): {result}")

        assert result["normalized_0_100"] == 100.0, (
            f"Compliant fixture should score 100 but got {result['normalized_0_100']}"
        )

    def test_violation_has_more_public_failures_than_compliant(
        self, checkov_public_storage, checkov_compliant
    ):
        """Violation fixture must have strictly more public-access failures."""
        viol_fails = PUBLIC_BLOCK_CHECKS & failed_ids(checkov_public_storage)
        comp_fails = PUBLIC_BLOCK_CHECKS & failed_ids(checkov_compliant)

        print(f"\nPublic-access failures — violation: {len(viol_fails)}, "
              f"compliant: {len(comp_fails)}")

        assert len(viol_fails) > len(comp_fails), (
            "Violation fixture should have more public-access failures than compliant"
        )
