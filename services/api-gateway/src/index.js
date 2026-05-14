import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";

const PORT = Number(process.env.PORT || 8080);
const services = {
  auth: process.env.AUTH_SERVICE_URL || "http://127.0.0.1:8001",
  users: process.env.USER_SERVICE_URL || "http://127.0.0.1:8002",
  orders: process.env.ORDER_SERVICE_URL || "http://127.0.0.1:8003",
  notify: process.env.NOTIFICATION_SERVICE_URL || "http://127.0.0.1:8004",
};

const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "512kb" }));

app.get("/health", async (_req, res) => {
  const checks = await Promise.allSettled([
    fetchJson(`${services.auth}/health`, "auth"),
    fetchJson(`${services.users}/health`, "users"),
    fetchJson(`${services.orders}/health`, "orders"),
    fetchJson(`${services.notify}/health`, "notify"),
  ]);
  const deps = checks.map((r, i) => {
    const name = ["auth", "users", "orders", "notify"][i];
    if (r.status === "fulfilled") return { service: name, ok: true, body: r.value };
    return { service: name, ok: false, error: String(r.reason?.message || r.reason) };
  });
  const ok = deps.every((d) => d.ok);
  res.status(ok ? 200 : 503).json({ service: "api-gateway", ok, dependencies: deps });
});

app.use(
  "/api/auth",
  createProxyMiddleware({
    target: services.auth,
    changeOrigin: true,
  }),
);

app.use(
  "/api/users",
  createProxyMiddleware({
    target: services.users,
    changeOrigin: true,
    pathRewrite: (path) => withBackendPrefix(path, "/users"),
  }),
);

app.use(
  "/api/orders",
  createProxyMiddleware({
    target: services.orders,
    changeOrigin: true,
    pathRewrite: (path) => withBackendPrefix(path, "/orders"),
  }),
);

app.use(
  "/api/notifications",
  createProxyMiddleware({
    target: services.notify,
    changeOrigin: true,
  }),
);

app.listen(PORT, "0.0.0.0", () => {
  console.log(`api-gateway listening on :${PORT}`);
});

function withBackendPrefix(path, prefix) {
  const tail = !path || path === "/" ? "" : path;
  return `${prefix}${tail}`;
}

async function fetchJson(url, label) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 2500);
  try {
    const r = await fetch(url, { signal: ctrl.signal });
    if (!r.ok) throw new Error(`${label} ${r.status}`);
    return await r.json();
  } finally {
    clearTimeout(t);
  }
}
