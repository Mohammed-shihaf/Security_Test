import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="order-service", version="0.1.0")
SERVICE = os.environ.get("SERVICE_NAME", "order-service")
USER_URL = os.environ.get("USER_SERVICE_URL", "http://127.0.0.1:8002")
NOTIFY_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://127.0.0.1:8004")

orders: dict[str, dict[str, Any]] = {
    "o1": {"id": "o1", "user_id": "u1", "items": [{"sku": "widget", "qty": 2}], "status": "created"},
    "o2": {"id": "o2", "user_id": "u2", "items": [{"sku": "gadget", "qty": 1}], "status": "shipped"},
}


@app.get("/health")
def health():
    return {"service": SERVICE, "ok": True}


@app.get("/orders")
def list_orders():
    return {"service": SERVICE, "orders": list(orders.values())}


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    row = orders.get(order_id)
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    return {"service": SERVICE, "order": row}


@app.post("/orders/{order_id}/submit")
async def submit_order(order_id: str):
    row = orders.get(order_id)
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    user_id = row.get("user_id")
    async with httpx.AsyncClient(timeout=3.0) as client:
        ur = await client.get(f"{USER_URL}/users/{user_id}")
        if ur.status_code != 200:
            raise HTTPException(status_code=400, detail="user_validation_failed")
        await client.post(
            f"{NOTIFY_URL}/enqueue",
            json={
                "channel": "email",
                "template": "order-submitted",
                "user_id": user_id,
                "order_id": order_id,
            },
        )
    row["status"] = "submitted"
    return {"service": SERVICE, "order": row}
