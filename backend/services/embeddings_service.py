from openai import OpenAI
import os
from typing import List, Dict, Any
import json
import logging
from datetime import datetime
from typing import Optional
from .vector_store_service import VectorStoreService
from llama_index.core import Document, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter

logger = logging.getLogger(__name__)

class EmbeddingsService:
    def __init__(self):
        """Initialize the OpenAI client and LlamaIndex settings"""
        # Get API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        try:
            # Initialize OpenAI client
            self.client = OpenAI(
                api_key=openai_api_key,
                timeout=60.0
            )
            
            # Initialize vector store service
            self.vector_store = VectorStoreService()
            
            # Initialize LlamaIndex settings
            self.embed_model = OpenAIEmbedding(
                model="text-embedding-3-large",
                dimensions=3072,
                embed_batch_size=10
            )
            Settings.embed_model = self.embed_model
            
            # Initialize node parser for chunking
            self.node_parser = SentenceSplitter(
                chunk_size=3000,
                chunk_overlap=200
            )
            
            logger.info("EmbeddingsService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize EmbeddingsService: {str(e)}")
            raise

    async def process_repository(
        self,
        repo_id: int,
        files: List[Dict[str, str]],
        status_callback: Optional[callable] = None
    ) -> bool:
        """
        Process an entire repository's files and store embeddings in vector store
        
        Args:
            repo_id: The repository ID (integer)
            files: List of files with name and content
            status_callback: Optional callback to update status
        
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Starting embedding process for repository {repo_id}")
            
            # Update status if callback provided
            if status_callback:
                await status_callback("processing", "Started embedding generation")
            
            # Generate embeddings for all files
            embeddings_list = await self.generate_embeddings(files)
            
            # Add repository metadata to each vector
            for vector in embeddings_list:
                vector["metadata"].update({
                    "repository_id": str(repo_id),
                    "file_path": vector["file_name"],
                    "chunk_content": vector["content"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Store vectors in Pinecone using vector store service
            await self.vector_store.upsert_vectors(
                repository_id=repo_id,
                vectors=embeddings_list
            )
            
            logger.info(f"Successfully processed repository {repo_id}")
            
            # Update status if callback provided
            if status_callback:
                await status_callback("completed", "Embedding generation completed")
            
            return True
            
        except Exception as e:
            error_msg = f"Error processing repository {repo_id}: {str(e)}"
            logger.error(error_msg)
            
            # Update status if callback provided
            if status_callback:
                await status_callback("failed", error_msg)
            
            raise

    async def generate_embeddings(self, files: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for repository files using LlamaIndex and OpenAI
        """
        embeddings_list = []

        try:
            for file in files:
                # Skip files with empty or invalid content
                if not file.get('content') or file['content'].strip() == '':
                    logger.info(f"Skipping empty file: {file.get('name', 'unknown')}")
                    continue

                # Create a Document for each file
                doc = Document(
                    text=file['content'],
                    metadata={"file_name": file['name']}
                )
                
                # Skip if document text is empty after processing
                if not doc.text or doc.text.strip() == '':
                    logger.info(f"Skipping file with empty text after processing: {file.get('name', 'unknown')}")
                    continue
                
                # Split document into nodes/chunks
                nodes = self.node_parser.get_nodes_from_documents([doc])
                
                # Skip if no valid nodes were created
                if not nodes:
                    logger.info(f"Skipping file with no valid chunks: {file.get('name', 'unknown')}")
                    continue
                
                # Generate embeddings for each chunk
                for node in nodes:
                    try:
                        # Skip empty nodes
                        if not node.text or node.text.strip() == '':
                            continue
                            
                        # Get embedding for the chunk
                        embedding = self.embed_model.get_text_embedding(
                            node.text
                        )
                        
                        # Add to results with metadata
                        embeddings_list.append({
                            "file_name": file["name"],
                            "embedding": embedding,
                            "content": node.text,
                            "metadata": {
                                "file_name": file["name"],
                                "chunk_index": len(embeddings_list),
                                "total_chunks": len(nodes)
                            }
                        })
                    except Exception as chunk_error:
                        logger.error(f"Error processing chunk in file {file['name']}: {str(chunk_error)}")
                        continue  # Skip this chunk and continue with others

            logger.info(f"Successfully generated embeddings for {len(files)} files")
            return embeddings_list

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    async def delete_repository_embeddings(self, repo_id: int) -> None:
        """
        Delete all embeddings for a repository
        
        Args:
            repo_id: Repository ID to delete embeddings for
        """
        try:
            await self.vector_store.delete_repository(repo_id)
            logger.info(f"Successfully deleted embeddings for repository {repo_id}")
        except Exception as e:
            logger.error(f"Error deleting repository embeddings: {str(e)}")
            raise