import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertRepositorySchema, insertMessageSchema } from "@shared/schema";
import { log } from "./vite";
import { createProxyMiddleware } from 'http-proxy-middleware';

export function registerRoutes(app: Express): Server {
  // Proxy all GitHub-related requests to FastAPI backend
  app.use('/api/github', createProxyMiddleware({
    target: 'http://localhost:8000',
    changeOrigin: true,
    pathRewrite: {
      '^/api/github': '/github'  // Rewrite /api/github to /github for FastAPI routes
    },
    proxyTimeout: 60000,  // 60 seconds timeout
    timeout: 60000,       // 60 seconds timeout
    onError: (err: Error, req: any, res: any) => {
      log(`Proxy error: ${err.message}`);
      res.status(504).json({
        message: "Failed to connect to GitHub service",
        details: err.message
      });
    }
  }));

  // Repository endpoints
  app.get("/api/repositories", async (_req, res) => {
    try {
      const repositories = await storage.getRepositories();
      res.json(repositories);
    } catch (error) {
      log(`Error fetching repositories: ${error}`);
      res.status(500).json({ 
        message: "Failed to fetch repositories",
        details: error instanceof Error ? error.message : String(error)
      });
    }
  });

  app.get("/api/repositories/:id", async (req, res) => {
    try {
      const repository = await storage.getRepository(Number(req.params.id));
      if (!repository) {
        return res.status(404).json({ message: "Repository not found" });
      }
      res.json(repository);
    } catch (error) {
      log(`Error fetching repository ${req.params.id}: ${error}`);
      res.status(500).json({ 
        message: "Failed to fetch repository",
        details: error instanceof Error ? error.message : String(error)
      });
    }
  });

  app.post("/api/repositories", async (req, res) => {
    try {
      const data = insertRepositorySchema.parse(req.body);
      const repository = await storage.createRepository(data);
      res.status(201).json(repository);
    } catch (error) {
      log(`Error creating repository: ${error}`);
      res.status(400).json({ 
        message: "Invalid repository data",
        details: error instanceof Error ? error.message : String(error)
      });
    }
  });

  // Messages endpoints
  app.get("/api/repositories/:id/messages", async (req, res) => {
    try {
      const messages = await storage.getMessages(Number(req.params.id));
      res.json(messages);
    } catch (error) {
      log(`Error fetching messages for repository ${req.params.id}: ${error}`);
      res.status(500).json({ 
        message: "Failed to fetch messages",
        details: error instanceof Error ? error.message : String(error)
      });
    }
  });

  app.post("/api/repositories/:id/messages", async (req, res) => {
    try {
      const data = insertMessageSchema.parse({
        ...req.body,
        repositoryId: Number(req.params.id),
      });
      const message = await storage.createMessage(data);
      res.status(201).json(message);
    } catch (error) {
      log(`Error creating message for repository ${req.params.id}: ${error}`);
      res.status(400).json({ 
        message: "Invalid message data",
        details: error instanceof Error ? error.message : String(error)
      });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}