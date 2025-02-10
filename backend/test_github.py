import asyncio
import logging
import os
from services.github_service import GitHubService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_github_service():
    try:
        # Check environment
        logger.info("Checking environment...")
        if 'GITHUB_TOKEN' in os.environ:
            logger.info("GITHUB_TOKEN found in environment")
        elif 'REPLIT_GITHUB_TOKEN' in os.environ:
            logger.info("REPLIT_GITHUB_TOKEN found in environment")
        else:
            logger.error("No GitHub token found in environment!")
            raise ValueError("Please set GITHUB_TOKEN in Replit secrets")

        # Initialize the service
        logger.info("Initializing GitHub service...")
        github_service = GitHubService()
        
        # Test URL
        test_url = "https://github.com/MikeC-A6/GitHubCloner"
        logger.info(f"Testing with URL: {test_url}")
        
        # Get repository data
        logger.info("Fetching repository data...")
        repo_data = await github_service.get_repository_data(test_url)
        
        # Log the results
        logger.info("Repository data fetched successfully:")
        logger.info(f"Name: {repo_data.get('name')}")
        logger.info(f"Owner: {repo_data.get('owner')}")
        logger.info(f"Description: {repo_data.get('description')}")
        logger.info(f"Number of files: {len(repo_data.get('files', []))}")
        
        return repo_data
    except Exception as e:
        logger.error(f"Error testing GitHub service: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(test_github_service())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        exit(1) 