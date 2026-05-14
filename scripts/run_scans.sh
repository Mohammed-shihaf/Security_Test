#!/usr/bin/env bash
# Local scan driver (POSIX). Install: gitleaks, checkov, trufflehog — see README.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "=== Gitleaks (repo gate; benchmarks/ allowlisted in .gitleaks.toml) ==="
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source . -v
else
  echo "gitleaks not found on PATH" >&2
fi

echo
echo "=== Gitleaks calibration (no benchmark allowlist) ==="
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source benchmarks/secrets --no-git --config .gitleaks-calibration.toml -v || true
fi

echo
echo "=== Checkov: compliant ==="
if command -v checkov >/dev/null 2>&1; then
  checkov -d iac/compliant --framework terraform -o cli --compact --soft-fail
else
  echo "checkov not found (pip install -r requirements-dev.txt)" >&2
fi

echo
echo "=== Checkov: intentional violations ==="
if command -v checkov >/dev/null 2>&1; then
  checkov -d benchmarks/iac/violations --framework terraform -o cli --compact --soft-fail
fi

echo
echo "=== TruffleHog (exclude benchmark secrets path) ==="
if command -v trufflehog >/dev/null 2>&1; then
  trufflehog git "file://$ROOT" --only-verified=false --exclude-paths=benchmarks/secrets || true
else
  echo "trufflehog not found on PATH" >&2
fi
