import { repositories, messages, type Repository, type InsertRepository, type Message, type InsertMessage } from "@shared/schema";
import { db } from "./db";
import { eq } from "drizzle-orm";

export interface IStorage {
  // Repository operations
  getRepository(id: number): Promise<Repository | undefined>;
  getRepositories(): Promise<Repository[]>;
  createRepository(repo: InsertRepository): Promise<Repository>;
  updateRepository(id: number, updates: Partial<Repository>): Promise<Repository | undefined>;
  
  // Message operations
  getMessages(repositoryId: number): Promise<Message[]>;
  createMessage(message: InsertMessage): Promise<Message>;
}

export class DatabaseStorage implements IStorage {
  async getRepository(id: number): Promise<Repository | undefined> {
    const [repo] = await db.select().from(repositories).where(eq(repositories.id, id));
    return repo;
  }

  async getRepositories(): Promise<Repository[]> {
    return await db.select().from(repositories);
  }

  async createRepository(repo: InsertRepository): Promise<Repository> {
    const [created] = await db.insert(repositories).values(repo).returning();
    return created;
  }

  async updateRepository(id: number, updates: Partial<Repository>): Promise<Repository | undefined> {
    const [updated] = await db
      .update(repositories)
      .set(updates)
      .where(eq(repositories.id, id))
      .returning();
    return updated;
  }

  async getMessages(repositoryId: number): Promise<Message[]> {
    return await db
      .select()
      .from(messages)
      .where(eq(messages.repositoryId, repositoryId))
      .orderBy(messages.timestamp);
  }

  async createMessage(message: InsertMessage): Promise<Message> {
    const [created] = await db.insert(messages).values(message).returning();
    return created;
  }
}

export const storage = new DatabaseStorage();
