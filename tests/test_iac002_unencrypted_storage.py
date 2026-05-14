"""
Whitebox tests — IAC-002: Unencrypted Storage Detection
========================================================
Metric:  IAC-002  |  L5: Unencrypted Storage Count
Formula: Encryption_Deficit_Score = Count(Unencrypted_Resources)*25
Score:   MAX(0, 100 − Encryption_Deficit_Score)
Checks:  CKV_AWS_17 (RDS storage_encrypted=false)
         CKV_AWS_19 (S3 server-side encryption)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from normalize_metrics import iac_002  # noqa: E402

from tests.helpers import (
    compliance_score,
    failed_ids,
    passed_ids,
    print_check_summary,
    COMPLIANT_DIR,
    VIOLATION_FILES,
)

# Checkov check IDs for encryption-at-rest
RDS_ENCRYPTED_CHECK = "CKV_AWS_16"   # RDS storage_encrypted (at rest)
S3_ENCRYPTED_CHECK = "CKV_AWS_19"    # S3 default encryption
ENCRYPTION_CHECKS = {RDS_ENCRYPTED_CHECK, S3_ENCRYPTED_CHECK}

pytestmark = pytest.mark.iac002


class TestUnencryptedStorageDetection:
    """Verify that storage resources lacking encryption-at-rest are flagged."""

    def test_unencrypted_rds_is_detected(self, checkov_unencrypted_storage):
        """
        unencrypted_rds.tf sets storage_encrypted = false.
        Checkov MUST report CKV_AWS_17 as failed.
        """
        fails = failed_ids(checkov_unencrypted_storage)
        print("\nFailed checks on unencrypted_rds.tf:")
        print_check_summary(checkov_unencrypted_storage, "violation")

        assert RDS_ENCRYPTED_CHECK in fails, (
            f"CKV_AWS_16 not in failed checks — unencrypted RDS not flagged.\n"
            f"Failed: {sorted(fails)}"
        )

    def test_violation_fixture_produces_failures(self, checkov_unencrypted_storage):
        """The violation fixture must generate at least one failed check."""
        fails = failed_ids(checkov_unencrypted_storage)
        assert fails, "Checkov found zero violations on unencrypted_rds.tf"

    def test_compliant_s3_encryption_passes(self, checkov_compliant):
        """
        minimal.tf has aws_s3_bucket_server_side_encryption_configuration.
        CKV_AWS_19 must NOT be in failed checks for the compliant dir.
        """
        fails = failed_ids(checkov_compliant)
        print(f"\nS3 encryption check in compliant dir: "
              f"{'FAIL' if S3_ENCRYPTED_CHECK in fails else 'PASS'}")

        assert S3_ENCRYPTED_CHECK not in fails, (
            "Compliant S3 fixture incorrectly fails encryption check CKV_AWS_19"
        )

    def test_compliant_has_no_rds_encryption_violation(self, checkov_compliant):
        """
        minimal.tf has no RDS instance, so CKV_AWS_17 must not appear as failed.
        """
        fails = failed_ids(checkov_compliant)
        assert RDS_ENCRYPTED_CHECK not in fails, (
            "CKV_AWS_17 unexpectedly appeared in compliant fixture failures"
        )

    def test_iac002_score_for_violation_fixture(self, checkov_unencrypted_storage):
        """
        IAC-002 score must be < 100 when unencrypted resources are present.
        Score formula: MAX(0, 100 − Count(Unencrypted_Resources)*25)
        """
        fails = failed_ids(checkov_unencrypted_storage)
        unencrypted_count = len(ENCRYPTION_CHECKS & fails)

        result = iac_002(unencrypted_count)
        print(f"\nIAC-002 score (violation fixture): {result}")

        assert result["normalized_0_100"] < 100, (
            "Score should be <100 when unencrypted resources are detected"
        )
        assert result["raw"]["Encryption_Deficit_Score"] > 0

    def test_iac002_score_for_compliant_fixture(self, checkov_compliant):
        """IAC-002 score must be 100 when all storage resources are encrypted."""
        fails = failed_ids(checkov_compliant)
        unencrypted_count = len(ENCRYPTION_CHECKS & fails)

        result = iac_002(unencrypted_count)
        print(f"\nIAC-002 score (compliant fixture): {result}")

        assert result["normalized_0_100"] == 100.0, (
            f"Compliant fixture should score 100 but got {result['normalized_0_100']}"
        )
