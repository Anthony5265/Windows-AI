/* ESM server */
import http from "node:http";
import { URL, fileURLToPath } from "node:url";
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..");
const BIN = path.resolve(ROOT, "bin", "wai.js");
const LOGS = path.resolve(ROOT, "logs");
function ymdLocal() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${dd}`;
}
function log(line) {
  const stamp = new Date().toISOString();
  const file = path.join(LOGS, `agent-${ymdLocal()}.log`);
  fs.appendFileSync(file, `[${stamp}] ${line}\n`);
  fs.appendFileSync(
    path.join(LOGS, "agent-latest.log"),
    `[${stamp}] ${line}\n`,
  );
}
function runWai(args, body) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [BIN, ...args], {
      cwd: ROOT,
      stdio: ["pipe", "pipe", "pipe"],
    });
    let out = "",
      err = "";
    if (body) child.stdin.write(body);
    child.stdin.end();
    child.stdout.on("data", (d) => (out += d.toString()));
    child.stderr.on("data", (d) => (err += d.toString()));
    child.on("close", (code) =>
      resolve({ code, out: out.trim(), err: err.trim() }),
    );
  });
}
async function handle(req, res) {
  const u = new URL(req.url, "http://localhost");
  const method = req.method || "GET";
  const chunks = [];
  req.on("data", (c) => chunks.push(c));
  req.on("end", async () => {
    const bodyStr = Buffer.concat(chunks).toString("utf8");
    try {
      if (u.pathname === "/health") {
        res.writeHead(200, { "content-type": "application/json" });
        return res.end(JSON.stringify({ ok: true, time: Date.now() }));
      }
      if (u.pathname === "/ask" && method === "POST") {
        const { prompt } = JSON.parse(bodyStr || "{}");
        const r = await runWai(["ask", prompt ?? ""]);
        log(`/ask code=${r.code} bytes=${r.out.length}`);
        res.writeHead(r.code === 0 ? 200 : 500, {
          "content-type": "application/json",
        });
        return res.end(JSON.stringify(r));
      }
      if (u.pathname === "/sh" && method === "POST") {
        const { command } = JSON.parse(bodyStr || "{}");
        const r = await runWai(["sh", command ?? ""]);
        log(`/sh code=${r.code} bytes=${r.out.length}`);
        res.writeHead(r.code === 0 ? 200 : 500, {
          "content-type": "application/json",
        });
        return res.end(JSON.stringify(r));
      }
      if (u.pathname === "/file/write" && method === "POST") {
        const { path: fp, content } = JSON.parse(bodyStr || "{}");
        const r = await runWai(["file:write", fp ?? "", content ?? ""]);
        log(`/file/write code=${r.code} -> ${fp}`);
        res.writeHead(r.code === 0 ? 200 : 500, {
          "content-type": "application/json",
        });
        return res.end(JSON.stringify(r));
      }
      if (u.pathname === "/file/read" && method === "POST") {
        const { path: fp } = JSON.parse(bodyStr || "{}");
        const r = await runWai(["file:read", fp ?? ""]);
        log(`/file/read code=${r.code} -> ${fp}`);
        res.writeHead(r.code === 0 ? 200 : 500, {
          "content-type": "application/json",
        });
        return res.end(JSON.stringify(r));
      }
      res.writeHead(404, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: "not_found" }));
    } catch (e) {
      log(`ERR ${e.stack || e}`);
      res.writeHead(500, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: String(e) }));
    }
  });
}
function parseListen() {
  const arg = process.argv.find((a) => a.startsWith("--listen=")) ?? "";
  const val = arg.split("=")[1] ?? process.env.WAI_LISTEN ?? "127.0.0.1:15777";
  const [host, portStr] = val.split(":");
  const port = Number(portStr) || 15777;
  return { host, port };
}
const { host, port } = parseListen();
const server = http.createServer(handle);
server.listen(port, host, () => {
  log(`server_up ${host}:${port}`);
  console.log(JSON.stringify({ ok: true, host, port }));
});
