import { pgTable, text, serial, jsonb, timestamp, boolean, index } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const repositories = pgTable(
  "repositories",
  {
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
    vectorized: boolean("vectorized").notNull().default(false),
    errorMessage: text("error_message"),
  },
  (table) => ({
    statusIdx: index("repositories_status_idx").on(table.status),
    vectorizedIdx: index("repositories_vectorized_idx").on(table.vectorized),
  })
);

export const messages = pgTable("messages", {
  id: serial("id").primaryKey(),
  repositoryId: serial("repository_id").references(() => repositories.id),
  role: text("role").notNull(),
  content: text("content").notNull(),
  timestamp: timestamp("timestamp").notNull().defaultNow(),
});

export const insertRepositorySchema = createInsertSchema(repositories, {
  url: z.string(),
  name: z.string(),
  owner: z.string(),
  description: z.string().optional(),
  files: z.array(z.object({
    name: z.string(),
    content: z.string()
  })),
  status: z.string(),
  branch: z.string(),
  path: z.string(),
  vectorized: z.boolean().optional()
});

export const insertMessageSchema = createInsertSchema(messages, {
  repositoryId: z.number(),
  role: z.string(),
  content: z.string()
});

export type Repository = typeof repositories.$inferSelect;
export type InsertRepository = z.infer<typeof insertRepositorySchema>;
export type Message = typeof messages.$inferSelect;
export type InsertMessage = z.infer<typeof insertMessageSchema>;