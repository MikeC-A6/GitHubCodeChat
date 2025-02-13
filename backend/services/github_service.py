import aiohttp
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import os
from typing import Dict, List, Any
from os import environ
import re
import logging
from ..utils.file_filter import filter_repository_files

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self):
        # Get token from environment variables or Replit secrets
        github_token = os.environ.get('GITHUB_TOKEN') or environ.get('REPLIT_GITHUB_TOKEN')
        
        # Log token presence (not the actual token)
        if not github_token:
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
        Parse GitHub URL to extract {owner, name, branch, path}.
        e.g. https://github.com/owner/repo/tree/my-branch/src
        """
        if not url.startswith("https://github.com/"):
            raise ValueError("Invalid GitHub URL. Must start with 'https://github.com/'")

        url = url.rstrip('/')
        parts = url.split('/')
        if len(parts) < 5:
            raise ValueError("Invalid GitHub URL. Must be in format: https://github.com/owner/repo[/tree/branch/path]")

        owner = parts[3]
        repo = parts[4]
        branch = "main"
        path = ""

        if len(parts) > 5 and parts[5] == "tree":
            # At least: https://github.com/owner/repo/tree/branch
            if len(parts) < 7:
                raise ValueError("Invalid GitHub URL. Missing branch name after '/tree/'")
            branch = parts[6]
            if len(parts) > 7:
                path = '/'.join(parts[7:])  # e.g. src/something

        return {
            "owner": owner,
            "name": repo,
            "branch": branch,
            "path": path
        }

    async def fetch_repository(self, url: str) -> Dict[str, Any]:
        """
        Public method to fetch an entire repo (metadata + all files recursively).
        """
        logger.info("=== Starting GitHub repository fetch (recursive) ===")
        logger.info(f"URL: {url}")

        # 1. Parse the GitHub URL
        repo_info = self._parse_github_url(url)

        # 2. Fetch the entire tree from the branch/path
        logger.info(f"Fetching entire tree for {repo_info}")
        all_files = await self._fetch_tree(
            owner=repo_info["owner"],
            name=repo_info["name"],
            branch=repo_info["branch"],
            path=repo_info["path"],  # could be empty or a subdirectory
        )

        # 3. Filter out ignored files
        filtered_files = filter_repository_files(all_files)
        logger.info(f"Filtered out {len(all_files) - len(filtered_files)} ignored files")
        logger.info(f"Remaining files to process: {len(filtered_files)}")

        # 4. Return a dict with metadata + filtered files
        return {
            "url": url,
            "owner": repo_info["owner"],
            "name": repo_info["name"],
            "description": "",  # can fetch separately if desired
            "files": filtered_files,
            "path": repo_info["path"],
            "branch": repo_info["branch"],
            "status": "processed",
        }

    async def _fetch_tree(
        self,
        owner: str,
        name: str,
        branch: str,
        path: str,
    ) -> List[Dict[str, str]]:
        """
        Recursively fetches all files (blobs) under the given path (tree).
        """
        files_collected: List[Dict[str, str]] = []

        # Build an expression for GitHub's GraphQL
        # "branch:path/to/directory" or just "branch:" for the repo root
        expression = f"{branch}:{path}" if path else f"{branch}:"
        logger.debug(f"_fetch_tree() expression = {expression}")

        # 1. Query the current level (the "tree" for the given path)
        query = gql("""
            query($owner: String!, $name: String!, $expression: String!) {
                repository(owner: $owner, name: $name) {
                    object(expression: $expression) {
                        ... on Tree {
                            entries {
                                name
                                type
                                oid
                                object {
                                    ... on Blob {
                                        text
                                        byteSize
                                        isBinary
                                    }
                                    ... on Tree {
                                        entries {
                                            name
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """)

        variables = {
            "owner": owner,
            "name": name,
            "expression": expression
        }

        try:
            result = await self.client.execute_async(query, variable_values=variables)

            # 2. Extract the top-level entries from the response
            repository = result.get("repository")
            if not repository or not repository.get("object"):
                # This can happen if the path doesn't exist, or it's an empty directory
                return files_collected  # Return empty

            entries = repository["object"].get("entries", [])

            # 3. Loop over entries. If it's a blob, we store it. If it's a tree, recurse.
            for entry in entries:
                entry_type = entry["type"]
                entry_name = entry["name"]

                if entry_type == "blob":
                    # It's a file. Save its text
                    blob = entry["object"]
                    if blob and "text" in blob:
                        # Construct the raw GitHub URL
                        raw_url = f"https://raw.githubusercontent.com/{owner}/{name}/{branch}/{path}/{entry_name}".lstrip("/")
                        
                        # Construct the GitHub web interface URL
                        file_path = f"{path}/{entry_name}".lstrip("/")
                        github_url = f"https://github.com/{owner}/{name}/blob/{branch}/{file_path}"
                        
                        files_collected.append({
                            "name": file_path,  # Full relative path
                            "content": blob["text"],
                            "url": raw_url,  # Raw content URL
                            "github_url": github_url,  # GitHub web interface URL
                            "size": blob.get("byteSize", 0),
                            "is_binary": blob.get("isBinary", False),
                            "object_id": entry.get("oid")
                        })

                elif entry_type == "tree":
                    # It's a subdirectory. Recurse into it.
                    sub_path = f"{path}/{entry_name}".strip("/")
                    logger.debug(f"Recursing into subdirectory: {sub_path}")
                    sub_files = await self._fetch_tree(owner, name, branch, sub_path)
                    files_collected.extend(sub_files)

            return files_collected
        except Exception as e:
            msg = f"GitHub GraphQL query failed at path='{path}': {str(e)}"
            logger.error(msg)
            raise ValueError(msg)