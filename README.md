# Security_Test — Whitebox / static repository security metrics lab

This repository is a **deliberately small lab** for measuring static (no running application) security controls aligned to typical **OWASP**, **PCI-DSS**, **FERPA/COPPA**, **GDPR**, and **SOC 2** evidence expectations. Scans target **source**, **IaC**, **git metadata**, **config**, and **dependency manifests**.

## Layout

| Path | Purpose |
|------|---------|
| `services/` | **Microservices** — each has its own `Dockerfile`; `docker compose` wires the mesh. |
| `contracts/events/` | Lightweight JSON Schema stubs for cross-service event contracts. |
| `app/` | Clean sample tree — **must stay free of real secrets** (production-style gate). |
| `iac/compliant/` | Reference Terraform meant to pass most IaC checks (still tune for your org). |
| `benchmarks/secrets/` | Synthetic “leaks” for **detector calibration** only (allowlisted for the main Gitleaks gate — see below). |
| `benchmarks/iac/violations/` | Intentional IaC issues (open SG, unencrypted RDS, public S3) for **IAC-001…003** tooling. |
| `metrics/registry.yaml` | Machine-readable L1–L5 metric definitions, thresholds, and normalization formulas. |
| `scripts/normalize_metrics.py` | Deterministic **0–100** scores from raw counts (your spreadsheet formulas). |
| `.github/workflows/whitebox-metrics.yml` | CI wiring for **Gitleaks**, **Checkov**, **Trufflehog**, plus benchmark jobs. |

## Metric quick map (your framework)

Secrets / credentials

- **SEC-001** — Gitleaks — *Secrets Exposed in Code Count* — `MAX(0, 100 − Secrets_Count×50)` — target **0** findings in production paths.
- **SEC-002** — detect-secrets (pre-commit) — *Blocked Secret Commit Count* — gate **100%** block rate; see `/.pre-commit-config.yaml` and `requirements-dev.txt`.
- **SEC-003** — Trufflehog — *Historical Secret Exposure Count* — `MAX(0, 100 − Historical×40)` — CI excludes `benchmarks/secrets/` via `--exclude-paths` so synthetic fixtures do not pollute history metrics.

IaC

- **IAC-001** — Open firewall / SG to `0.0.0.0/0` on non-80/443 — `MAX(0, 100 − (Open_Ports×30 + Wildcard_CIDR×15))`.
- **IAC-002** — Unencrypted storage — `MAX(0, 100 − Unencrypted×25)`.
- **IAC-003** — Public buckets — `MAX(0, 100 − PublicBuckets×40)`.
- **IAC-004** — CIS-style Checkov pass rate — gate **≥ 95%** (map failed/passed checks from Checkov JSON to your CIS ruleset subset).

SOC 2 repository metadata (API — not fully automatable without tokens)

- **SOC-001** — Unreviewed merges / branch protection — `MAX(0, 100 − Bypass_Rate×20)` — example: `scripts/check_branch_protection.ps1` plus GitHub audit log / PR export.
- **SOC-002** — Overprivileged collaborators / bots — `MAX(0, 100 − Overprivileged×20)` — example: `scripts/list_repo_collaborators.ps1` with a read-only token, then map `permissions.admin` / `permissions.push` to your RBAC model.

Full field-by-field alignment (tools, artifacts, frequencies) lives in [`metrics/registry.yaml`](metrics/registry.yaml).

## Gitleaks allowlist strategy (important)

- **Main gate** uses `.gitleaks.toml`, which **allowlists** `benchmarks/secrets/` so the default `gitleaks detect --source .` run can stay green while still hosting calibration payloads.
- **Calibration** uses `.gitleaks-calibration.toml` (**no path allowlist**) when scanning only `benchmarks/secrets/`. The GitHub Action job `SEC-001 — Benchmark calibration` asserts **≥ 1** finding so scanners are not silently blind.

If your Gitleaks version stops matching the synthetic file, edit `benchmarks/secrets/synthetic-leaks.env` (keep payloads **fake**).

## Microservices (Docker)

| Service | Stack | Internal port | Role |
|---------|-------|---------------|------|
| `api-gateway` | Node 20 + Express | 8080 (published) | Edge HTTP + reverse proxy to other services |
| `auth-service` | Python 3.12 + FastAPI | 8001 | Stub session/token endpoints (lab only — not real IdP) |
| `user-service` | Node 20 + Express | 8002 | In-memory user catalogue |
| `order-service` | Python 3.12 + FastAPI | 8003 | Orders + calls **user** + **notification** on submit |
| `notification-service` | Node 20 + Express | 8004 | In-process “queue” for outbound notifications |

**Run the stack**

Copy [`.env.example`](.env.example) to `.env` if you want to override ports. By default the gateway is published on **`18080`** (avoids common conflicts with local apps on `8080`).

```powershell
docker compose build
docker compose up -d
# optional: make health   (requires make + curl on PATH)
curl http://127.0.0.1:18080/health
curl http://127.0.0.1:18080/api/users
curl http://127.0.0.1:18080/api/orders
curl -X POST http://127.0.0.1:18080/api/orders/o1/submit
```

Public API is only the gateway (host port from `GATEWAY_PUBLIC_PORT`, default **18080** → container **8080**). Other containers stay on the internal Docker network.

## Local usage

**Python normalization (examples):**

```powershell
python scripts\normalize_metrics.py --secrets-count 0 --json
python scripts\normalize_metrics.py --open-sg 1 --wildcard-cidr 0 --public-buckets 1 --unencrypted 1 --json
python scripts\normalize_metrics.py --cis-pass 48 --cis-total 50 --json
```

**Pre-commit (SEC-002):**

```powershell
pip install -r requirements-dev.txt
pre-commit install
```

**Scans:**

```powershell
.\scripts\run_scans.ps1 -BenchmarkSecrets -BenchmarkIac -CompliantIac
# or
bash scripts/run_scans.sh
```

## CI

Workflow: [`.github/workflows/whitebox-metrics.yml`](.github/workflows/whitebox-metrics.yml)

- **Gitleaks** — production-style full tree (benchmark secrets path allowlisted).
- **Gitleaks benchmark** — confirms detectors fire on `benchmarks/secrets/`.
- **Checkov** — `iac/compliant` (soft-fail for developer ergonomics; remove `--soft-fail` when you want a hard gate) and JSON capture for violations.
- **Trufflehog** — diff-oriented scan with `benchmarks/secrets` excluded from paths.

## Compliance note

`benchmarks/` contains **intentionally weak** configurations. Treat this repo as a **measurement harness**, not a deployment template. For real systems, pair these scans with policy-as-code, code review, and production verification.
