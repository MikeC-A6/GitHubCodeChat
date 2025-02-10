import express, { type Request, Response, NextFunction } from "express";
import { registerRoutes } from "./routes";
import { setupVite, serveStatic, log } from "./vite";
import { createProxyMiddleware, type Options } from "http-proxy-middleware";
import { spawn } from "child_process";
import path from "path";
import { IncomingMessage, ServerResponse, ClientRequest } from "http";

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
  app.use("/api", createProxyMiddleware({
    target: "http://localhost:8000",
    changeOrigin: true,
    pathRewrite: {
      '^/api': ''  // Remove /api prefix when forwarding
    },
    onProxyReq: (proxyReq: ClientRequest, req: express.Request, res: express.Response) => {
      // Log the original request details
      log(`Proxying ${req.method} ${req.url}`, "fastapi");
      log(`Request headers: ${JSON.stringify(req.headers)}`, "fastapi");
      
      // If there's a request body, forward it correctly
      if (req.body) {
        const bodyData = JSON.stringify(req.body);
        log(`Request body: ${bodyData}`, "fastapi");
        
        // Update header
        proxyReq.setHeader('Content-Type', 'application/json');
        proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyData));
        
        // Write body to request
        proxyReq.write(bodyData);
        proxyReq.end();
      }
    },
    onProxyRes: (proxyRes: IncomingMessage, req: express.Request, res: express.Response) => {
      log(`Proxy response: ${proxyRes.statusCode} for ${req.method} ${req.url}`, "fastapi");
      
      // Log response body for debugging
      let responseBody = '';
      proxyRes.on('data', (chunk) => {
        responseBody += chunk;
      });
      proxyRes.on('end', () => {
        log(`Response body: ${responseBody}`, "fastapi");
      });
    },
    onError: (err: Error, req: express.Request, res: express.Response) => {
      log(`Proxy error: ${err.message}`, "fastapi");
      res.writeHead(500, {
        'Content-Type': 'application/json',
      });
      res.end(JSON.stringify({ 
        error: "Failed to connect to Python backend",
        details: err.message 
      }));
    }
  } as Options));

  // Add request logging middleware
  app.use((req: Request, res: Response, next: NextFunction) => {
    log(`Incoming request: ${req.method} ${req.url}`, "express");
    next();
  });

  // Response logging middleware
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