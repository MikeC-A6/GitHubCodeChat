from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from backend.api.routes import github, chat
from backend.services.db_service import DatabaseService
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Initialize FastAPI with timeout configuration
app = FastAPI()

# Initialize services
db_service = DatabaseService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("FastAPI server starting up...")

    # Initialize database
    try:
        logger.info("Initializing database...")
        await db_service.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")

    # Log registered routes
    logger.info("Routes registered:")
    for route in app.routes:
        logger.info(f"  {route.methods} {route.path}")

# Configure CORS for production and development
REPLIT_URL = os.environ.get('REPLIT_URL', '')
if not REPLIT_URL and 'REPL_ID' in os.environ:
    REPL_OWNER = os.environ.get('REPL_OWNER', '')
    REPL_SLUG = os.environ.get('REPL_SLUG', '')
    REPLIT_URL = f"https://{REPL_SLUG}.{REPL_OWNER}.repl.co"

origins = [
    REPLIT_URL,
    "https://*.replit.dev",
    "https://*.repl.co",
    "https://*.replit.app",
    "http://localhost:3000",
    "http://localhost:5000",
    "http://0.0.0.0:5000",
    "http://127.0.0.1:5000",
]

logger.info(f"Configured CORS origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include routers with proper prefixes
app.include_router(github.router, prefix="/github", tags=["github"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        timeout_keep_alive=120,  # 2 minutes timeout
        access_log=True
    )