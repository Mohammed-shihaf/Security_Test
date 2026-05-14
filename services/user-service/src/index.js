import express from "express";

const PORT = Number(process.env.PORT || 8002);
const SERVICE = process.env.SERVICE_NAME || "user-service";

const users = [
  { id: "u1", email: "alice@example.test", name: "Alice" },
  { id: "u2", email: "bob@example.test", name: "Bob" },
];

const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "256kb" }));

app.get("/health", (_req, res) => {
  res.json({ service: SERVICE, ok: true });
});

app.get("/users", (_req, res) => {
  res.json({ service: SERVICE, users });
});

app.get("/users/:id", (req, res) => {
  const u = users.find((x) => x.id === req.params.id);
  if (!u) return res.status(404).json({ error: "not_found" });
  res.json({ service: SERVICE, user: u });
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`${SERVICE} listening on :${PORT}`);
});
