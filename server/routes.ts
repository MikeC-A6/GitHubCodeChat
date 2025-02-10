import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertRepositorySchema, insertMessageSchema } from "@shared/schema";

export function registerRoutes(app: Express): Server {
  // Repository endpoints
  app.get("/api/repositories", async (_req, res) => {
    try {
      const repositories = await storage.getRepositories();
      res.json(repositories);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch repositories" });
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
      res.status(500).json({ message: "Failed to fetch repository" });
    }
  });

  app.post("/api/repositories", async (req, res) => {
    try {
      const data = insertRepositorySchema.parse(req.body);
      const repository = await storage.createRepository(data);
      res.status(201).json(repository);
    } catch (error) {
      res.status(400).json({ message: "Invalid repository data" });
    }
  });

  // Messages endpoints
  app.get("/api/repositories/:id/messages", async (req, res) => {
    try {
      const messages = await storage.getMessages(Number(req.params.id));
      res.json(messages);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch messages" });
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
      res.status(400).json({ message: "Invalid message data" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
