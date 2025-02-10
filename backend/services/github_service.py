import aiohttp
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import os
from typing import Dict, List, Any
from os import environ
import re
import logging

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self):
        # Get token from Replit secrets
        github_token = os.environ.get('GITHUB_TOKEN') or environ.get('REPLIT_GITHUB_TOKEN')
        
        # Log token presence (not the actual token)
        if github_token:
            logger.info("GitHub token found in environment")
        else:
            logger.error("GitHub token not found in environment variables")
            raise ValueError("GitHub token not found in environment variables. Please set GITHUB_TOKEN in Replit secrets.")
            
        # Initialize GraphQL client
        try:
            self.transport = AIOHTTPTransport(
                url='https://api.github.com/graphql',
                headers={'Authorization': f'Bearer {github_token}'}
            )
            self.client = Client(transport=self.transport)
            logger.info("GitHub GraphQL client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {str(e)}")
            raise

    async def get_repository_data(self, url: str) -> Dict[str, Any]:
        """
        Get repository data including metadata and files
        """
        try:
            logger.info(f"=== Starting GitHub repository fetch ===")
            logger.info(f"URL: {url}")
            
            # Parse the GitHub URL
            logger.info("Parsing GitHub URL...")
            repo_info = self._parse_github_url(url)
            logger.info(f"Parsed repository info: {repo_info}")
            
            # Fetch repository data
            logger.info("Fetching repository data from GitHub API...")
            repo_data = await self.fetch_repository(url)
            logger.info(f"Successfully fetched repository: {repo_data.get('name', 'unknown')}")
            logger.info(f"Number of files: {len(repo_data.get('files', []))}")
            logger.info("=== GitHub repository fetch completed ===")
            
            return repo_data
        except Exception as e:
            logger.error("=== GitHub repository fetch failed ===")
            logger.error(f"Error fetching repository data: {str(e)}", exc_info=True)
            raise

    def _parse_github_url(self, url: str) -> Dict[str, str]:
        """
        Parse GitHub URL to extract owner, repo name, branch, and path
        Example URLs:
        - https://github.com/owner/repo
        - https://github.com/owner/repo/tree/branch
        - https://github.com/owner/repo/tree/branch/path/to/dir
        """
        if not url.startswith("https://github.com/"):
            raise ValueError("Invalid GitHub URL. Must start with 'https://github.com/'")

        url = url.rstrip('/')
        parts = url.split('/')
        
        if len(parts) < 5:
            raise ValueError("Invalid GitHub URL. Must be in format: https://github.com/owner/repo[/tree/branch/path]")
        
        # Basic owner/repo extraction
        owner = parts[3]
        repo = parts[4]
        
        # Default values
        branch = "main"
        path = ""
        
        # Check if URL contains tree (indicating branch and path)
        if len(parts) > 5:
            if parts[5] != "tree":
                raise ValueError("Invalid GitHub URL. Directory path must start with '/tree/'")
            if len(parts) < 7:
                raise ValueError("Invalid GitHub URL. Missing branch name after '/tree/'")
            branch = parts[6]
            path = '/'.join(parts[7:]) if len(parts) > 7 else ""
        
        logger.info(f"Parsed GitHub URL - owner: {owner}, repo: {repo}, branch: {branch}, path: {path}")
        return {
            "owner": owner,
            "name": repo,
            "branch": branch,
            "path": path
        }

    async def fetch_repository(self, url: str) -> Dict[str, Any]:
        """
        Fetch repository metadata and file contents using GitHub GraphQL API
        """
        try:
            # Parse the GitHub URL
            repo_info = self._parse_github_url(url)
            
            # Construct the expression for the specific path
            expression = f"{repo_info['branch']}:{repo_info['path']}" if repo_info['path'] else f"{repo_info['branch']}:"
            logger.info(f"Using Git expression: {expression}")
    
            # GraphQL query to fetch repository data
            query = gql("""
                query($owner: String!, $name: String!, $expression: String!) {
                    repository(owner: $owner, name: $name) {
                        name
                        description
                        object(expression: $expression) {
                            ... on Tree {
                                entries {
                                    name
                                    type
                                    object {
                                        ... on Blob {
                                            text
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            """)
    
            # Execute the query
            variables = {
                "owner": repo_info["owner"],
                "name": repo_info["name"],
                "expression": expression
            }
            
            logger.info(f"Executing GraphQL query with variables: {variables}")
            result = await self.client.execute_async(query, variable_values=variables)
            
            if not result or "repository" not in result:
                raise ValueError(f"Repository {repo_info['owner']}/{repo_info['name']} not found")
            
            if not result["repository"]["object"]:
                raise ValueError(f"Directory '{repo_info['path']}' not found in branch '{repo_info['branch']}'")
    
            # Process and format the response
            files = self._process_files(result["repository"]["object"]["entries"])
            logger.info(f"Processed {len(files)} files from repository")
    
            return {
                "url": url,
                "owner": repo_info["owner"],
                "name": repo_info["name"],
                "description": result["repository"].get("description", ""),
                "files": files,
                "path": repo_info["path"],
                "branch": repo_info["branch"],
                "status": "processed"
            }
    
        except ValueError as e:
            logger.error(f"Value error in fetch_repository: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in fetch_repository: {str(e)}")
            raise ValueError(f"Failed to fetch repository: {str(e)}")

    def _process_files(self, entries: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Process repository entries and extract file contents
        """
        files = []
        for entry in entries:
            if entry["type"] == "blob" and entry["object"] and "text" in entry["object"]:
                files.append({
                    "name": entry["name"],
                    "content": entry["object"]["text"]
                })
        return files