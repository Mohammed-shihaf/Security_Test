# Secret-detection benchmarks (SEC-001 calibration)

Synthetic strings for **local scanner calibration only**. Paths here are allowlisted in `.gitleaks.toml` so the default repo gate on `app/` stays clean.

To prove detectors fire, run:

```bash
gitleaks detect --source benchmarks/secrets --no-git -v
```

Do not copy these values into `app/`.
