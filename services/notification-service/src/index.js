import express from "express";

const PORT = Number(process.env.PORT || 8004);
const SERVICE = process.env.SERVICE_NAME || "notification-service";

/** @type {{ id: string; payload: unknown; created_at: string }[]} */
const queue = [];

const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "256kb" }));

app.get("/health", (_req, res) => {
  res.json({ service: SERVICE, ok: true, queue_depth: queue.length });
});

app.post("/enqueue", (req, res) => {
  const item = {
    id: `n${queue.length + 1}`,
    payload: req.body ?? {},
    created_at: new Date().toISOString(),
  };
  queue.push(item);
  res.status(202).json({ service: SERVICE, accepted: true, id: item.id });
});

app.get("/queue", (_req, res) => {
  res.json({ service: SERVICE, items: queue.slice(-50) });
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`${SERVICE} listening on :${PORT}`);
});
