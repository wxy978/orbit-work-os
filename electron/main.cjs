const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("child_process");
const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const path = require("path");

let apiProcess;
let webServer;

function contentType(file) {
  const ext = path.extname(file).toLowerCase();
  return ({ ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon", ".woff2": "font/woff2" })[ext] || "application/octet-stream";
}

function startFrontend(root) {
  webServer = http.createServer((req, res) => {
    const requestPath = decodeURIComponent((req.url || "/").split("?")[0]);
    let relative = requestPath === "/" ? "index.html" : requestPath.replace(/^\/+/, "");
    if (!path.extname(relative)) relative = path.join(relative, "index.html");
    const target = path.resolve(root, relative);
    if (!target.startsWith(path.resolve(root))) { res.writeHead(403); res.end("Forbidden"); return; }
    fs.readFile(target, (error, data) => {
      if (error) { res.writeHead(404); res.end("Not found"); return; }
      res.writeHead(200, { "Content-Type": contentType(target), "Cache-Control": "no-cache" }); res.end(data);
    });
  });
  return new Promise((resolve, reject) => { webServer.once("error", reject); webServer.listen(3000, "127.0.0.1", resolve); });
}

function desktopSecret(userData) {
  const file = path.join(userData, "app-secret.txt");
  if (!fs.existsSync(file)) fs.writeFileSync(file, crypto.randomBytes(48).toString("hex"), { mode: 0o600 });
  return fs.readFileSync(file, "utf8").trim();
}

function startBackend(userData) {
  const executable = app.isPackaged ? path.join(process.resourcesPath, "backend", "orbit-api.exe") : path.join(__dirname, "..", "dist", "orbit-api.exe");
  const dataDir = path.join(userData, "data"); const uploadDir = path.join(userData, "uploads");
  fs.mkdirSync(dataDir, { recursive: true }); fs.mkdirSync(uploadDir, { recursive: true });
  const databasePath = path.join(dataDir, "orbit.db").replace(/\\/g, "/");
  apiProcess = spawn(executable, [], { windowsHide: true, env: { ...process.env, DATABASE_URL: `sqlite:///${databasePath}`, UPLOAD_DIR: uploadDir, JWT_SECRET: desktopSecret(userData), FRONTEND_URL: "http://localhost:3000", DEMO_AI_ENABLED: "true" } });
  apiProcess.on("error", (error) => dialog.showErrorBox("Orbit Work OS", `后端服务启动失败：${error.message}`));
}

async function waitForApi() {
  for (let i = 0; i < 50; i++) {
    try { const response = await fetch("http://127.0.0.1:8000/health"); if (response.ok) return; } catch {}
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  throw new Error("内置服务启动超时");
}

async function createWindow() {
  const frontend = app.isPackaged ? path.join(process.resourcesPath, "frontend") : path.join(__dirname, "..", "out");
  startBackend(app.getPath("userData"));
  await Promise.all([startFrontend(frontend), waitForApi()]);
  const win = new BrowserWindow({ width: 1440, height: 920, minWidth: 1080, minHeight: 700, backgroundColor: "#f8fafc", title: "Orbit Work OS", webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true } });
  await win.loadURL("http://localhost:3000/dashboard/");
}

app.whenReady().then(() => createWindow().catch(error => dialog.showErrorBox("Orbit Work OS", error.message)));
app.on("window-all-closed", () => app.quit());
app.on("before-quit", () => { if (webServer) webServer.close(); if (apiProcess) apiProcess.kill(); });
