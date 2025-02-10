import aiohttp
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import os

class GitHubService:
    def __init__(self):
        transport = AIOHTTPTransport(
            url='https://api.github.com/graphql',
            headers={'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}'}
        )
        self.client = Client(transport=transport)

    async def fetch_repository(self, url: str):
        # Parse owner and name from URL
        parts = url.strip('/').split('/')
        owner = parts[-2]
        name = parts[-1]

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

        result = await self.client.execute_async(
            query,
            variable_values={"owner": owner, "name": name}
        )

        return {
            "owner": owner,
            "name": name,
            "description": result["repository"]["description"],
            "files": self._process_files(result["repository"]["object"]["entries"])
        }

    def _process_files(self, entries):
        files = []
        for entry in entries:
            if entry["type"] == "blob":
                files.append({
                    "name": entry["name"],
                    "content": entry["object"]["text"]
                })
        return files
