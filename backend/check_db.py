import asyncio
from services.db_service import DatabaseService
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_db():
    try:
        db = DatabaseService()
        await db.initialize()
        
        # Get the first repository
        repo = await db.get_repository(1)
        
        if repo:
            print("\nRepository #1:")
            for key, value in repo.items():
                if key == 'files':
                    print(f"\nFiles ({len(value)} total):")
                    for file in value:
                        print(f"  - {file['name']}")
                else:
                    print(f"{key}: {value}")
        else:
            print("No repository found with ID 1")
            
        await db.close()
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(check_db()) 