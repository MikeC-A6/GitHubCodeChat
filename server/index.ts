// server/index.ts
import express, { type Request, Response, NextFunction } from "express";
import { registerRoutes } from "./routes";
import { setupVite, serveStatic, log } from "./vite";
import { createProxyMiddleware, type Options } from "http-proxy-middleware";
import { spawn } from "child_process";
import path from "path";
import { IncomingMessage, ServerResponse, ClientRequest } from "http";

// ------------------------------------------
// Initialize Express App
// ------------------------------------------
const app = express();

// ------------------------------------------
// Start FastAPI via Uvicorn (spawn Python process)
// ------------------------------------------
log("Starting FastAPI backend...", "fastapi");

const pythonProcess = spawn("python3", [
  "-m",
  "uvicorn",
  "backend.api.main:app",
  "--host",
  "0.0.0.0",
  "--port",
  "8000",
  "--reload",
  "--log-level",
  "info",
], {
  cwd: process.cwd(),
  env: {
    ...process.env,
    PYTHONPATH: process.cwd(),
  },
});

pythonProcess.stdout.on("data", (data) => {
  log(`Python: ${data}`, "fastapi");
});

pythonProcess.stderr.on("data", (data) => {
  log(`Python error: ${data}`, "fastapi");
});

pythonProcess.on("error", (error) => {
  log(`Failed to start Python process: ${error}`, "fastapi");
});

pythonProcess.on("close", (code) => {
  if (code !== 0) {
    log(`Python process exited with code ${code}`, "fastapi");
  }
});

// ------------------------------------------
// Request Logging Middleware
// ------------------------------------------
app.use((req: Request, res: Response, next: NextFunction) => {
  log(`Incoming request: ${req.method} ${req.url}`, "express");
  next();
});

// ------------------------------------------
// Body Parsing Middleware
// ------------------------------------------
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

// ------------------------------------------
// Proxy Configuration for FastAPI
// ------------------------------------------
const FASTAPI_URL = process.env.NODE_ENV === 'production'
  ? 'http://0.0.0.0:8000'  // Production
  : 'http://0.0.0.0:8000'; // Development

app.use('/api', createProxyMiddleware({
  target: FASTAPI_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/api': '',  // Remove /api prefix when forwarding to FastAPI
  },
  onProxyReq: (proxyReq: ClientRequest) => {
    log(`Proxying ${proxyReq.method} request to: ${proxyReq.path}`, "fastapi");
  },
  onProxyRes: (proxyRes: IncomingMessage) => {
    log(`Proxy response status: ${proxyRes.statusCode}`, "fastapi");
    // Log headers for debugging
    log(`Response headers: ${JSON.stringify(proxyRes.headers)}`, "fastapi");
  },
  onError: (err: Error, req: Request, res: Response) => {
    log(`Proxy error: ${err.message}`, "fastapi");
    // Log the full error stack for debugging
    log(`Full error: ${err.stack}`, "fastapi");
    res.status(504).json({
      message: "Failed to connect to backend service",
      details: err.message,
      path: req.url
    });
  },
  proxyTimeout: 300000, // 5 minutes - chat responses can take longer
  timeout: 300000,      // 5 minutes
} as Options));

// ------------------------------------------
// Register Routes (which includes proxy configuration)
// ------------------------------------------
const server = registerRoutes(app);

// ------------------------------------------
// Vite / Static Files Setup
// ------------------------------------------
if (app.get("env") === "development") {
  setupVite(app, server);
} else {
  serveStatic(app);
}

// ------------------------------------------
// Listen on PORT (Replit or fallback 5000)
// ------------------------------------------
const PORT = parseInt(process.env.PORT || "5000", 10);
server.listen(PORT, "0.0.0.0", () => {
  log(`Express server listening on port ${PORT}`, "express");
});