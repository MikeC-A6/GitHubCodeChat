import aiohttp
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import os
from typing import Dict, List, Any

class GitHubService:
    def __init__(self):
        self.transport = AIOHTTPTransport(
            url='https://api.github.com/graphql',
            headers={'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}'}
        )
        self.client = Client(transport=self.transport)

    async def fetch_repository(self, url: str) -> Dict[str, Any]:
        """
        Fetch repository metadata and file contents using GitHub GraphQL API
        """
        # Parse owner and name from URL
        parts = url.strip('/').split('/')
        owner = parts[-2]
        name = parts[-1]

        # GraphQL query to fetch repository data
        query = gql("""
            query($owner: String!, $name: String!) {
                repository(owner: $owner, name: $name) {
                    name
                    description
                    object(expression: "HEAD:") {
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
            "owner": owner,
            "name": name
        }

        try:
            result = await self.client.execute_async(query, variable_values=variables)

            # Process and format the response
            files = self._process_files(result["repository"]["object"]["entries"])

            return {
                "owner": owner,
                "name": name,
                "description": result["repository"]["description"],
                "files": files,
                "status": "processed"
            }

        except Exception as e:
            print(f"Error fetching repository: {str(e)}")
            raise

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