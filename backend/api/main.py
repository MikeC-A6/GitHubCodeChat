from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import github, chat
from backend.services.db_service import DatabaseService
import logging
import sys

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "ok"}

# Remove /api prefix since Express will add it
app.include_router(github.router, prefix="/github", tags=["github"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI server starting up...")
    
    # Initialize database
    try:
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

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
