# SOC-001 example: query GitHub branch protection (requires gh CLI + auth).
# Usage: gh auth login
#        .\scripts\check_branch_protection.ps1 -Owner "myorg" -Repo "Security_Test" -Branch "main"

param(
    [Parameter(Mandatory = $true)][string]$Owner,
    [Parameter(Mandatory = $true)][string]$Repo,
    [Parameter(Mandatory = $false)][string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

Write-Host "Fetching branch protection for $Owner/$Repo @ $Branch ..."
gh api repos/$Owner/$Repo/branches/$Branch/protection --jq . 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "No branch protection or insufficient token scopes (needs admin:read for private repos)."
    exit 1
}

Write-Host "`nFor SOC-001, map API fields to your policy:"
Write-Host "- required_pull_request_reviews.required_approving_review_count"
Write-Host "- enforce_admins, restrictions, allow_force_pushes (should align with change control)"
Write-Host "Compute Bypass_Rate from PR merge audit data (not fully expressible in branch protection JSON alone)."
