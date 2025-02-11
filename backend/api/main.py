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
        # Don't raise the error - let the app start even if DB init fails
        # The error will be handled when making DB calls

    # Log registered routes
    logger.info("Routes registered:")
    for route in app.routes:
        logger.info(f"  {route.methods} {route.path}")

# Get the Replit URL from environment or construct it
REPLIT_URL = os.environ.get('REPLIT_URL', '')
if not REPLIT_URL and 'REPL_ID' in os.environ:
    REPL_OWNER = os.environ.get('REPL_OWNER', '')
    REPL_SLUG = os.environ.get('REPL_SLUG', '')
    REPLIT_URL = f"https://{REPL_SLUG}.{REPL_OWNER}.repl.co"

# Configure CORS for Replit environment
origins = [
    REPLIT_URL,
    "https://*.replit.dev",
    "https://*.repl.co",
    "https://*.replit.app",  # Add support for production domain
    "http://localhost:3000",
    "http://localhost:5000",
]

logger.info(f"Configured CORS origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
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
        access_log=True
    )