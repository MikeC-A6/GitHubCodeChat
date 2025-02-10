import express, { type Request, Response, NextFunction } from "express";
import { registerRoutes } from "./routes";
import { setupVite, serveStatic, log } from "./vite";
import { createProxyMiddleware, type Options } from "http-proxy-middleware";
import { spawn } from "child_process";
import path from "path";

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

// Start FastAPI backend
log("Starting FastAPI backend...", "fastapi");

const pythonProcess = spawn("python3", [
  "-m", "uvicorn",
  "backend.api.main:app",
  "--host", "0.0.0.0",
  "--port", "8000",
  "--reload",  // Add auto-reload for development
  "--log-level", "info"
], {
  cwd: process.cwd(),  // Ensure we're in the right directory
  env: {
    ...process.env,
    PYTHONPATH: process.cwd()  // Add current directory to Python path
  }
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

// Wait for FastAPI to start before setting up proxy
setTimeout(() => {
  // Add proxy middleware for FastAPI backend
  const proxyOptions: Options = {
    target: "http://localhost:8000",
    changeOrigin: true,
    pathRewrite: {
      '^/api': ''  // Remove /api prefix when forwarding
    },
    onProxyError: (err, req, res) => {
      log(`Proxy error: ${err}`, "fastapi");
      res.writeHead(500, {
        'Content-Type': 'application/json',
      });
      res.end(JSON.stringify({ error: "Failed to connect to Python backend" }));
    }
  };

  app.use("/api", createProxyMiddleware(proxyOptions));

  app.use((req, res, next) => {
    const start = Date.now();
    const path = req.path;
    let capturedJsonResponse: Record<string, any> | undefined = undefined;

    const originalResJson = res.json;
    res.json = function (bodyJson, ...args) {
      capturedJsonResponse = bodyJson;
      return originalResJson.apply(res, [bodyJson, ...args]);
    };

    res.on("finish", () => {
      const duration = Date.now() - start;
      if (path.startsWith("/api")) {
        let logLine = `${req.method} ${path} ${res.statusCode} in ${duration}ms`;
        if (capturedJsonResponse) {
          logLine += ` :: ${JSON.stringify(capturedJsonResponse)}`;
        }
        log(logLine);
      }
    });

    next();
  });

  // Register other routes
  const server = registerRoutes(app);

  if (app.get("env") === "development") {
    setupVite(app, server);
  } else {
    serveStatic(app);
  }

  const PORT = 5000;
  server.listen(PORT, "0.0.0.0", () => {
    log(`serving on port ${PORT}`);
  });
}, 2000);  // Give FastAPI 2 seconds to start