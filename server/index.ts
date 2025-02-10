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

// Parse JSON bodies so we can log them (and optionally rewrite them for the proxy)
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

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
// Request Logging Middleware (place BEFORE proxy)
// ------------------------------------------
app.use((req: Request, res: Response, next: NextFunction) => {
  log(`Incoming request: ${req.method} ${req.url}`, "express");
  next();
});

// Response Logging Middleware (also place BEFORE proxy if you want to measure total time)
app.use((req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  const path = req.path;

  res.on("finish", () => {
    const duration = Date.now() - start;
    let logLine = `${req.method} ${path} ${res.statusCode} in ${duration}ms`;
    log(logLine, "express");
  });

  next();
});

// ------------------------------------------
// Proxy Middleware for FastAPI
// ------------------------------------------
app.use(
  "/api",
  createProxyMiddleware({
    target: "http://localhost:8000",
    changeOrigin: true,
    pathRewrite: {
      "^/api": "", // remove '/api' prefix
    },
    onProxyReq: (
      proxyReq: ClientRequest,
      req: express.Request,
      res: express.Response
    ) => {
      // Log details of the proxied request
      log(`Proxying ${req.method} ${req.url}`, "fastapi");
      log(`Request headers: ${JSON.stringify(req.headers)}`, "fastapi");

      // Only rewrite the request body if it's a method that can have a JSON body
      if (
        ["POST", "PUT", "PATCH"].includes(req.method.toUpperCase()) &&
        req.body
      ) {
        const bodyData = JSON.stringify(req.body);
        log(`Request body: ${bodyData}`, "fastapi");

        proxyReq.setHeader("Content-Type", "application/json");
        proxyReq.setHeader("Content-Length", Buffer.byteLength(bodyData));
        proxyReq.write(bodyData);
        proxyReq.end();
      }
    },
    onProxyRes: (
      proxyRes: IncomingMessage,
      req: express.Request,
      res: express.Response
    ) => {
      log(
        `Proxy response: ${proxyRes.statusCode} for ${req.method} ${req.url}`,
        "fastapi"
      );

      let responseBody = "";
      proxyRes.on("data", (chunk) => {
        responseBody += chunk;
      });
      proxyRes.on("end", () => {
        log(`Response body: ${responseBody}`, "fastapi");
      });
    },
    onError: (err: Error, req: express.Request, res: express.Response) => {
      log(`Proxy error: ${err.message}`, "fastapi");
      res.writeHead(500, {
        "Content-Type": "application/json",
      });
      res.end(
        JSON.stringify({
          error: "Failed to connect to Python backend",
          details: err.message,
        })
      );
    },
  } as Options)
);

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