from typing import Dict, Any, List
import asyncpg
import os
import json
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Base exception for database operations"""
    pass

class DatabaseService:
    def __init__(self):
        """Initialize database connection"""
        self.pool = None
        # Get database URL from environment, with a fallback for Replit
        self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            # Construct URL from Replit secrets
            username = os.environ.get("PGUSER", "postgres")
            password = os.environ.get("PGPASSWORD", "postgres")
            host = os.environ.get("PGHOST", "localhost")
            port = os.environ.get("PGPORT", "5432")
            database = os.environ.get("PGDATABASE", "postgres")

            self.db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            logger.info("Using Replit database configuration")

        logger.info("Database URL configured")

    async def initialize(self):
        """Initialize the database with schema"""
        try:
            # Create the pool with SSL required for Replit
            self.pool = await asyncpg.create_pool(
                self.db_url,
                ssl="require",  # Required for Replit's PostgreSQL
                min_size=1,     # Minimum number of connections
                max_size=10,    # Maximum number of connections
                command_timeout=60  # Increase timeout to 60 seconds
            )

            schema_path = Path("schema.sql")
            if schema_path.exists():
                schema_sql = schema_path.read_text()
                async with self.pool.acquire() as conn:
                    await conn.execute(schema_sql)
                logger.info("Database schema initialized successfully")
            else:
                raise DatabaseError("Schema file not found at schema.sql")

        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise DatabaseError(f"Failed to initialize database: {str(e)}")

    async def get_pool(self):
        """Get or create connection pool"""
        if self.pool is None:
            try:
                self.pool = await asyncpg.create_pool(
                    self.db_url,
                    ssl="require",  # Required for Replit's PostgreSQL
                    min_size=1,     # Minimum number of connections
                    max_size=10,    # Maximum number of connections
                    command_timeout=60  # Increase timeout to 60 seconds
                )
            except Exception as e:
                logger.error(f"Failed to create database pool: {str(e)}")
                raise DatabaseError(f"Failed to create database pool: {str(e)}")
        return self.pool

    async def create_repository(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new repository record"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            try:
                # Convert files to JSON string for storage
                files_json = json.dumps(data["files"])

                # Insert repository
                row = await conn.fetchrow("""
                    INSERT INTO repositories (
                        url, name, owner, description, files, 
                        status, branch, path, vectorized
                    ) VALUES (
                        $1, $2, $3, $4, $5, 
                        $6, $7, $8, $9
                    )
                    RETURNING 
                        id, url, name, owner, description, 
                        files, status, branch, path, vectorized,
                        processed_at, created_at
                    """,
                    data["url"],
                    data["name"],
                    data["owner"],
                    data.get("description", ""),
                    files_json,
                    data.get("status", "pending"),
                    data.get("branch", "main"),
                    data.get("path", ""),
                    data.get("vectorized", False)
                )

                result = {
                    "id": row["id"],
                    "url": row["url"],
                    "name": row["name"],
                    "owner": row["owner"],
                    "description": row["description"],
                    "files": json.loads(row["files"]),
                    "status": row["status"],
                    "branch": row["branch"],
                    "path": row["path"],
                    "vectorized": row["vectorized"],
                    "processed_at": row["processed_at"],
                    "created_at": row["created_at"]
                }
                logger.info(f"Successfully created repository: {result['owner']}/{result['name']}")
                return result

            except Exception as e:
                logger.error(f"Failed to create repository: {str(e)}")
                raise DatabaseError(f"Failed to create repository: {str(e)}")

    async def get_repositories(self) -> List[Dict[str, Any]]:
        """Get all repositories"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            try:
                rows = await conn.fetch("""
                    SELECT 
                        id, url, name, owner, description,
                        files, status, branch, path, vectorized,
                        processed_at, created_at
                    FROM repositories 
                    ORDER BY created_at DESC
                    """)

                results = [{
                    "id": row["id"],
                    "url": row["url"],
                    "name": row["name"],
                    "owner": row["owner"],
                    "description": row["description"],
                    "files": json.loads(row["files"]),
                    "status": row["status"],
                    "branch": row["branch"],
                    "path": row["path"],
                    "vectorized": row["vectorized"],
                    "processed_at": row["processed_at"],
                    "created_at": row["created_at"]
                } for row in rows]

                logger.info(f"Successfully fetched {len(results)} repositories")
                return results

            except Exception as e:
                logger.error(f"Failed to fetch repositories: {str(e)}")
                raise DatabaseError(f"Failed to fetch repositories: {str(e)}")

    async def get_repository(self, id: int) -> Dict[str, Any]:
        """Get a repository by ID"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            try:
                row = await conn.fetchrow("""
                    SELECT 
                        id, url, name, owner, description,
                        files, status, branch, path, vectorized,
                        processed_at
                    FROM repositories 
                    WHERE id = $1
                    """, 
                    id
                )
                
                if not row:
                    return None

                return {
                    "id": row["id"],
                    "url": row["url"],
                    "name": row["name"],
                    "owner": row["owner"],
                    "description": row["description"],
                    "files": json.loads(row["files"]),
                    "status": row["status"],
                    "branch": row["branch"],
                    "path": row["path"],
                    "vectorized": row["vectorized"],
                    "processed_at": row["processed_at"]
                }

            except Exception as e:
                raise DatabaseError(f"Failed to get repository: {str(e)}")

    async def update_repository_status(
        self, 
        id: int, 
        status: str,
        vectorized: bool = None
    ) -> Dict[str, Any]:
        """Update repository status"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            try:
                update_fields = ["status = $2"]
                params = [id, status]
                
                if vectorized is not None:
                    update_fields.append("vectorized = $3")
                    params.append(vectorized)
                
                if status == "processed":
                    update_fields.append("processed_at = CURRENT_TIMESTAMP")
                
                query = f"""
                    UPDATE repositories 
                    SET {', '.join(update_fields)}
                    WHERE id = $1
                    RETURNING 
                        id, url, name, owner, description,
                        files, status, branch, path, vectorized,
                        processed_at, created_at
                """
                
                row = await conn.fetchrow(query, *params)
                
                return {
                    "id": row["id"],
                    "url": row["url"],
                    "name": row["name"],
                    "owner": row["owner"],
                    "description": row["description"],
                    "files": json.loads(row["files"]),
                    "status": row["status"],
                    "branch": row["branch"],
                    "path": row["path"],
                    "vectorized": row["vectorized"],
                    "processed_at": row["processed_at"],
                    "created_at": row["created_at"]
                }

            except Exception as e:
                logger.error(f"Failed to update repository status: {str(e)}")
                raise DatabaseError(f"Failed to update repository status: {str(e)}")

    async def close(self):
        if self.pool:
            await self.pool.close()