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
  "--timeout-keep-alive",
  "120",  // Increase keep-alive timeout
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
// Request Logging Middleware (BEFORE proxy)
// ------------------------------------------
app.use((req: Request, res: Response, next: NextFunction) => {
  log(`Incoming request: ${req.method} ${req.url}`, "express");
  next();
});

// Wait for FastAPI to initialize
setTimeout(() => {
  // ------------------------------------------
  // Proxy Middleware for FastAPI (with improved configuration)
  // ------------------------------------------
  app.use(
    "/api",
    createProxyMiddleware({
      target: "http://localhost:8000",
      changeOrigin: true,
      pathRewrite: {
        "^/api": "", // remove '/api' prefix
      },
      // Increase timeouts
      proxyTimeout: 120000,
      timeout: 120000,
      onProxyReq: (proxyReq: ClientRequest, req: express.Request, res: express.Response) => {
        log(`Proxying ${req.method} ${req.url}`, "fastapi");
        // Ensure connection is kept alive
        proxyReq.setHeader('Connection', 'keep-alive');
      },
      onProxyRes: (proxyRes: IncomingMessage, req: express.Request, res: express.Response) => {
        log(`Proxy response: ${proxyRes.statusCode} for ${req.method} ${req.url}`, "fastapi");
      },
      onError: (err: Error, req: express.Request, res: express.Response) => {
        log(`Proxy error: ${err.message}`, "fastapi");
        res.status(500).json({ 
          error: "Failed to connect to Python backend", 
          details: err.message 
        });
      },
    } as Options)
  );
}, 5000); // Give FastAPI 5 seconds to initialize

// ------------------------------------------
// Body Parsing Middleware (AFTER proxy)
// ------------------------------------------
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

// ------------------------------------------
// Register Other Routes (if any)
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