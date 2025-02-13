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
                model="text-embedding-3-small",
                dimensions=1536,
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
        repo_name: str,
        files: List[Dict[str, str]],
        status_callback: Optional[callable] = None
    ) -> bool:
        """
        Process an entire repository's files and store embeddings in vector store
        
        Args:
            repo_id: The repository ID (integer)
            repo_name: The repository name (for ID generation and namespace)
            files: List of files with name, content, and metadata
            status_callback: Optional callback to update status
        
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Starting embedding process for repository {repo_id}")
            
            # Update status if callback provided
            if status_callback:
                await status_callback("processing", "Started embedding generation")
            
            # Clean repository name for namespace
            namespace = f"repo_{repo_name.lower().replace(' ', '_').replace('-', '_')}"
            
            # Generate embeddings for all files
            embeddings_list = await self.generate_embeddings(files, repo_name)
            
            # Add essential metadata to each vector
            for vector in embeddings_list:
                vector["metadata"].update({
                    "repository_id": str(repo_id),
                    "file_path": vector["file_name"],
                    "chunk_content": vector["content"],
                    "timestamp": datetime.utcnow().isoformat(),
                    # Add file-specific metadata
                    "file_url": vector["file_metadata"].get("url"),
                    "file_size": vector["file_metadata"].get("size"),
                    "file_is_binary": vector["file_metadata"].get("is_binary", False),
                    "file_object_id": vector["file_metadata"].get("object_id"),
                    "file_github_url": vector["file_metadata"].get("github_url")
                })
            
            # Store vectors in Pinecone using vector store service with namespace
            await self.vector_store.upsert_vectors(
                repository_id=repo_id,
                vectors=embeddings_list,
                namespace=namespace
            )
            
            logger.info(f"Successfully processed repository {repo_id} in namespace {namespace}")
            
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

    async def generate_embeddings(
        self, 
        files: List[Dict[str, str]], 
        repo_name: str
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for repository files using LlamaIndex and OpenAI
        
        Args:
            files: List of files with content and metadata
            repo_name: Repository name for ID generation
        """
        embeddings_list = []
        processed_files = 0
        skipped_files = 0
        total_chunks = 0
        
        # Clean repository name for ID generation
        clean_repo_name = repo_name.lower().replace(" ", "_").replace("-", "_")

        try:
            logger.info(f"Starting to process {len(files)} files")
            
            for file in files:
                # Skip files with empty or invalid content
                if not file.get('content') or file['content'].strip() == '':
                    logger.info(f"Skipping empty file: {file.get('name', 'unknown')}")
                    skipped_files += 1
                    continue

                logger.info(f"Processing file: {file.get('name', 'unknown')}")

                # Create a Document for each file
                doc = Document(
                    text=file['content'],
                    metadata={"file_name": file['name']}
                )
                
                # Skip if document text is empty after processing
                if not doc.text or doc.text.strip() == '':
                    logger.info(f"Skipping file with empty text after processing: {file.get('name', 'unknown')}")
                    skipped_files += 1
                    continue
                
                # Split document into nodes/chunks
                nodes = self.node_parser.get_nodes_from_documents([doc])
                
                # Skip if no valid nodes were created
                if not nodes:
                    logger.info(f"Skipping file with no valid chunks: {file.get('name', 'unknown')}")
                    skipped_files += 1
                    continue
                
                logger.info(f"File {file.get('name', 'unknown')} split into {len(nodes)} chunks")
                chunks_for_file = 0
                
                # Generate embeddings for each chunk
                for chunk_idx, node in enumerate(nodes, 1):
                    try:
                        # Skip empty nodes
                        if not node.text or node.text.strip() == '':
                            logger.info(f"Skipping empty chunk {chunk_idx} in file {file.get('name', 'unknown')}")
                            continue
                            
                        # Get embedding for the chunk
                        embedding = self.embed_model.get_text_embedding(
                            node.text
                        )
                        
                        # Create unique ID using file name and chunk index
                        clean_file_name = file["name"].replace("/", "_").replace(".", "_")
                        vector_id = f"{clean_repo_name}_{clean_file_name}_{chunk_idx}"
                        
                        # Add to results with metadata
                        embeddings_list.append({
                            "id": vector_id,
                            "file_name": file["name"],
                            "embedding": embedding,
                            "content": node.text,
                            "file_metadata": {
                                "url": file.get("url"),
                                "size": file.get("size"),
                                "is_binary": file.get("is_binary", False),
                                "object_id": file.get("object_id"),
                                "github_url": file.get("github_url")
                            },
                            "metadata": {
                                "file_name": file["name"],
                                "chunk_index": chunk_idx,
                                "total_chunks": len(nodes)
                            }
                        })
                        chunks_for_file += 1
                        total_chunks += 1
                        
                    except Exception as chunk_error:
                        logger.error(f"Error processing chunk {chunk_idx} in file {file['name']}: {str(chunk_error)}")
                        continue  # Skip this chunk and continue with others
                
                logger.info(f"Successfully processed {chunks_for_file} chunks for file {file.get('name', 'unknown')}")
                processed_files += 1

            logger.info(f"Embedding generation summary:")
            logger.info(f"Total files: {len(files)}")
            logger.info(f"Successfully processed files: {processed_files}")
            logger.info(f"Skipped files: {skipped_files}")
            logger.info(f"Total chunks generated: {total_chunks}")
            logger.info(f"Total embeddings created: {len(embeddings_list)}")
            return embeddings_list

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    async def delete_repository_embeddings(self, repo_id: int, repo_name: str) -> None:
        """
        Delete all embeddings for a repository
        
        Args:
            repo_id: Repository ID to delete embeddings for
            repo_name: Repository name for namespace
        """
        try:
            # Create namespace from repository name
            namespace = f"repo_{repo_name.lower().replace(' ', '_').replace('-', '_')}"
            
            await self.vector_store.delete_repository(repo_id, namespace)
            logger.info(f"Successfully deleted embeddings for repository {repo_id} from namespace {namespace}")
        except Exception as e:
            logger.error(f"Error deleting repository embeddings: {str(e)}")
            raise