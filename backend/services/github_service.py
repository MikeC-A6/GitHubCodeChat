import aiohttp
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import os
from typing import Dict, List, Any
from os import environ
import re

class GitHubService:
    def __init__(self):
        # Get token from Replit secrets
        github_token = environ.get('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GITHUB_TOKEN not found in environment variables")
            
        self.transport = AIOHTTPTransport(
            url='https://api.github.com/graphql',
            headers={'Authorization': f'Bearer {github_token}'}
        )
        self.client = Client(transport=self.transport)

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
    
            result = await self.client.execute_async(query, variable_values=variables)
            if not result or "repository" not in result:
                raise ValueError(f"Repository {repo_info['owner']}/{repo_info['name']} not found")
            
            if not result["repository"]["object"]:
                raise ValueError(f"Directory '{repo_info['path']}' not found in branch '{repo_info['branch']}'")
    
            # Process and format the response
            files = self._process_files(result["repository"]["object"]["entries"])
    
            return {
                "owner": repo_info["owner"],
                "name": repo_info["name"],
                "description": result["repository"].get("description", ""),
                "files": files,
                "path": repo_info["path"],
                "branch": repo_info["branch"],
                "status": "processed"
            }
    
        except ValueError as e:
            raise
        except Exception as e:
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