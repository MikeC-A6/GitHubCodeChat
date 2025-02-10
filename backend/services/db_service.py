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
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize database connection"""
        if not hasattr(self, 'initialized'):
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
            self.initialized = True

    @property
    def pool(self):
        """Get the connection pool, initializing it if necessary"""
        if self._pool is None:
            raise DatabaseError("Database not initialized. Call initialize() first.")
        return self._pool

    async def initialize(self):
        """Initialize the database with schema"""
        if self._pool is not None:
            logger.info("Database already initialized")
            return

        try:
            logger.info("Creating database pool...")
            # Create the pool with SSL required for Replit
            self._pool = await asyncpg.create_pool(
                self.db_url,
                ssl="require",  # Required for Replit's PostgreSQL
                min_size=1,     # Minimum number of connections
                max_size=10,    # Maximum number of connections
                command_timeout=60  # Increase timeout to 60 seconds
            )
            logger.info("Database pool created successfully")

            # Look for schema.sql in the backend directory
            schema_paths = [
                Path("schema.sql"),
                Path("backend/schema.sql"),
                Path("../schema.sql"),
                Path(__file__).parent.parent / "schema.sql"
            ]

            schema_file = None
            for path in schema_paths:
                if path.exists():
                    schema_file = path
                    logger.info(f"Found schema file at: {path}")
                    break

            if schema_file:
                logger.info("Reading schema file...")
                schema_sql = schema_file.read_text()
                async with self._pool.acquire() as conn:
                    logger.info("Executing schema...")
                    await conn.execute(schema_sql)
                    logger.info("Schema executed successfully")
            else:
                logger.error("Could not find schema.sql file!")
                raise DatabaseError("Schema file not found")

        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise DatabaseError(f"Database initialization failed: {str(e)}")

    async def get_pool(self):
        """Get or create connection pool"""
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    self.db_url,
                    ssl="require",  # Required for Replit's PostgreSQL
                    min_size=1,     # Minimum number of connections
                    max_size=10,    # Maximum number of connections
                    command_timeout=60  # Increase timeout to 60 seconds
                )
            except Exception as e:
                logger.error(f"Failed to create database pool: {str(e)}")
                raise DatabaseError(f"Failed to create database pool: {str(e)}")
        return self._pool

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
        try:
            if not self._pool:
                raise DatabaseError("Database not initialized")

            async with self._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, url, name, owner, description, status, 
                           branch, path, processed_at, vectorized
                    FROM repositories
                    ORDER BY created_at DESC
                """)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching repositories: {str(e)}")
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
        if self._pool:
            await self._pool.close()

    async def store_repository(self, repo_data: Dict[str, Any]) -> int:
        """Store repository data and return the ID"""
        try:
            if not self._pool:
                raise DatabaseError("Database not initialized")

            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("""
                    INSERT INTO repositories (url, name, owner, description, files, branch, path)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """,
                    repo_data["url"],
                    repo_data["name"],
                    repo_data["owner"],
                    repo_data.get("description"),
                    json.dumps(repo_data["files"]),
                    repo_data.get("branch", "main"),
                    repo_data.get("path", "")
                )
                return row["id"]
        except Exception as e:
            logger.error(f"Error storing repository: {str(e)}")
            raise DatabaseError(f"Failed to store repository: {str(e)}")

    async def store_embeddings(self, repo_id: int, embeddings: List[Dict[str, Any]]) -> None:
        """Store embeddings for a repository"""
        try:
            if not self._pool:
                raise DatabaseError("Database not initialized")

            async with self._pool.acquire() as conn:
                await conn.execute("""
                    UPDATE repositories
                    SET vectorized = true,
                        processed_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, repo_id)
        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}")
            raise DatabaseError(f"Failed to store embeddings: {str(e)}")

    async def get_repository_files(self, repo_id: int) -> List[Dict[str, str]]:
        """Get files for a repository"""
        try:
            if not self._pool:
                raise DatabaseError("Database not initialized")

            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT files
                    FROM repositories
                    WHERE id = $1
                """, repo_id)
                
                if not row:
                    raise DatabaseError(f"Repository {repo_id} not found")
                
                return row["files"]
        except Exception as e:
            logger.error(f"Error fetching repository files: {str(e)}")
            raise DatabaseError(f"Failed to fetch repository files: {str(e)}")