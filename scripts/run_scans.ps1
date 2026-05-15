# Local driver for whitebox scans (install tools first — see README).
param(
    [switch]$BenchmarkSecrets,
    [switch]$BenchmarkIac,
    [switch]$CompliantIac
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

Write-Host "=== Gitleaks (production paths; benchmarks excluded via .gitleaks.toml) ===" 
if (Get-Command gitleaks -ErrorAction SilentlyContinue) {
    gitleaks detect --source . -v
} else {
    Write-Warning "gitleaks not in PATH"
}

if ($BenchmarkSecrets) {
    Write-Host "`n=== Gitleaks calibration on benchmarks/secrets (.gitleaks-calibration.toml) ===" 
    gitleaks detect --source benchmarks/secrets --no-git --config .gitleaks-calibration.toml -v
}

Write-Host "`n=== Checkov ===" 
if (Get-Command checkov -ErrorAction SilentlyContinue) {
    if ($BenchmarkIac) {
        checkov -d benchmarks/iac/violations --framework terraform -o cli
    }
    if ($CompliantIac) {
        checkov -d iac/compliant --framework terraform -o cli
    }
    if (-not $BenchmarkIac -and -not $CompliantIac) {
        checkov -d . --framework terraform --skip-path benchmarks/secrets -o cli
    }

    Write-Host "`n=== Checkov: IaC smoke bundles ===" 
    checkov -d iac/kubernetes --framework kubernetes -o cli --compact --soft-fail
    checkov -d iac/cloudformation --framework cloudformation -o cli --compact --soft-fail
    checkov -d iac/helm/smoke-chart --framework helm -o cli --compact --soft-fail
    checkov -d iac/ansible --framework ansible -o cli --compact --soft-fail
    checkov -d iac/bicep --framework bicep -o cli --compact --soft-fail
    Write-Host "`n=== Checkov: Dockerfiles (services/) ===" 
    checkov -d services --framework dockerfile -o cli --compact --soft-fail
} else {
    Write-Warning "checkov not in PATH (pip install checkov)"
}

Write-Host "`n=== Trufflehog (full git history) ===" 
if (Get-Command trufflehog -ErrorAction SilentlyContinue) {
    trufflehog git file://$root --only-verified=false
} else {
    Write-Warning "trufflehog not in PATH"
}
