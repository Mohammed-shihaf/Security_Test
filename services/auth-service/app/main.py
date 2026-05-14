import os
from fastapi import FastAPI

app = FastAPI(title="auth-service", version="0.1.0")
SERVICE = os.environ.get("SERVICE_NAME", "auth-service")


@app.get("/health")
def health():
    return {"service": SERVICE, "ok": True}


@app.post("/session", summary="Stub session (no real auth — lab only)")
def create_session():
    # Intentionally no secrets — return opaque placeholder for demos.
    return {
        "service": SERVICE,
        "token_type": "lab-stub",
        "expires_in_seconds": 3600,
        "subject": "demo-user",
    }
