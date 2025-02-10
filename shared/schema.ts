import { pgTable, text, serial, jsonb, timestamp, varchar } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const repositories = pgTable("repositories", {
  id: serial("id").primaryKey(),
  url: text("url").notNull(),
  name: text("name").notNull(),
  owner: text("owner").notNull(),
  description: text("description"),
  files: jsonb("files").notNull(),
  status: text("status").notNull().default("pending"),
  branch: text("branch").notNull().default("main"),
  path: text("path").notNull().default(""),
  processedAt: timestamp("processed_at"),
  embeddings: text("embeddings").array(),
});

export const messages = pgTable("messages", {
  id: serial("id").primaryKey(),
  repositoryId: serial("repository_id").references(() => repositories.id),
  role: text("role").notNull(),
  content: text("content").notNull(),
  timestamp: timestamp("timestamp").notNull().defaultNow(),
});

export const insertRepositorySchema = createInsertSchema(repositories).pick({
  url: true,
  name: true,
  owner: true,
  description: true,
  files: true,
  status: true,
  branch: true,
  path: true,
});

export const insertMessageSchema = createInsertSchema(messages).pick({
  repositoryId: true,
  role: true,
  content: true,
});

export type Repository = typeof repositories.$inferSelect;
export type InsertRepository = z.infer<typeof insertRepositorySchema>;
export type Message = typeof messages.$inferSelect;
export type InsertMessage = z.infer<typeof insertMessageSchema>;
