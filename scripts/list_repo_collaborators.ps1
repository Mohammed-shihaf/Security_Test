# SOC-002 example: list repo collaborators and roles (requires gh CLI + token with read:org if org repo).
param(
    [Parameter(Mandatory = $true)][string]$Owner,
    [Parameter(Mandatory = $true)][string]$Repo
)

$ErrorActionPreference = "Stop"
Write-Host "Collaborators for $Owner/$Repo (inspect admin/write for least-privilege reviews) ..."
gh api "repos/$Owner/$Repo/collaborators" --paginate
