"""
Pinecone Vector Database Provider Implementation

Provides Pinecone integration for vector search and knowledge retrieval.
"""

import os
from typing import List, Dict, Any, Optional
import logging
import asyncio
from pinecone import Pinecone, ServerlessSpec
import hashlib
import json

from ..interfaces import VectorDBInterface, Document

logger = logging.getLogger(__name__)


class PineconeVectorDB(VectorDBInterface):
    """Pinecone vector database implementation"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: str = "iseetutor",
        dimension: int = 384,  # all-MiniLM-L6-v2 dimension
        metric: str = "cosine",
        embedding_function: Optional[Any] = None
    ):
        """
        Initialize Pinecone vector database provider
        
        Args:
            api_key: Pinecone API key (defaults to env var)
            environment: Pinecone environment (defaults to env var)
            index_name: Name of the Pinecone index
            dimension: Vector dimension
            metric: Distance metric (cosine, euclidean, dotproduct)
            embedding_function: Function to generate embeddings
        """
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        
        if not self.api_key:
            raise ValueError("Pinecone API key is required")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric
        
        # Set up embedding function
        if embedding_function:
            self.embedding_function = embedding_function
        else:
            # Default to sentence-transformers
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_function = lambda texts: self.embedder.encode(texts).tolist()
        
        # Create or connect to index
        self._setup_index()
    
    def _setup_index(self):
        """Create index if it doesn't exist"""
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            
            if self.index_name not in [idx.name for idx in existing_indexes]:
                # Create new index
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=self.environment
                    )
                )
                logger.info(f"Created Pinecone index: {self.index_name}")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            
        except Exception as e:
            logger.error(f"Pinecone setup error: {str(e)}")
            raise
    
    async def index(
        self,
        documents: List[Dict[str, Any]],
        collection: str = "default"
    ) -> None:
        """
        Index documents in Pinecone
        
        Args:
            documents: List of documents with 'id', 'content', and 'metadata'
            collection: Collection name (used as namespace in Pinecone)
        """
        try:
            # Prepare vectors
            vectors = []
            
            for doc in documents:
                # Generate ID if not provided
                doc_id = doc.get('id', self._generate_id(doc['content']))
                
                # Generate embedding
                if isinstance(self.embedding_function, asyncio.coroutine):
                    embedding = await self.embedding_function(doc['content'])
                else:
                    # Run sync function in executor
                    loop = asyncio.get_event_loop()
                    embedding = await loop.run_in_executor(
                        None,
                        self.embedding_function,
                        [doc['content']]
                    )
                    embedding = embedding[0]
                
                # Prepare metadata
                metadata = doc.get('metadata', {})
                metadata['content'] = doc['content'][:1000]  # Store truncated content
                metadata['collection'] = collection
                
                vectors.append({
                    'id': doc_id,
                    'values': embedding,
                    'metadata': metadata
                })
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(
                    vectors=batch,
                    namespace=collection
                )
            
            logger.info(f"Indexed {len(documents)} documents in Pinecone")
            
        except Exception as e:
            logger.error(f"Pinecone indexing error: {str(e)}")
            raise
    
    async def search(
        self,
        query: str,
        collection: str = "default",
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Search for similar documents in Pinecone
        
        Args:
            query: Search query
            collection: Collection name (namespace)
            k: Number of results to return
            filter: Metadata filter
            
        Returns:
            List of matching documents
        """
        try:
            # Generate query embedding
            if isinstance(self.embedding_function, asyncio.coroutine):
                query_embedding = await self.embedding_function(query)
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                query_embedding = await loop.run_in_executor(
                    None,
                    self.embedding_function,
                    [query]
                )
                query_embedding = query_embedding[0]
            
            # Perform search
            results = self.index.query(
                vector=query_embedding,
                top_k=k,
                namespace=collection,
                filter=filter,
                include_metadata=True
            )
            
            # Convert to Document objects
            documents = []
            for match in results.matches:
                # Retrieve full content if needed
                content = match.metadata.get('content', '')
                
                # Remove internal metadata
                metadata = {k: v for k, v in match.metadata.items() 
                           if k not in ['content', 'collection']}
                
                documents.append(Document(
                    id=match.id,
                    content=content,
                    metadata=metadata,
                    score=match.score
                ))
            
            return documents
            
        except Exception as e:
            logger.error(f"Pinecone search error: {str(e)}")
            raise
    
    async def delete(
        self,
        ids: List[str],
        collection: str = "default"
    ) -> None:
        """
        Delete documents by ID from Pinecone
        
        Args:
            ids: List of document IDs to delete
            collection: Collection name (namespace)
        """
        try:
            self.index.delete(
                ids=ids,
                namespace=collection
            )
            logger.info(f"Deleted {len(ids)} documents from Pinecone")
            
        except Exception as e:
            logger.error(f"Pinecone deletion error: {str(e)}")
            raise
    
    async def update(
        self,
        id: str,
        document: Dict[str, Any],
        collection: str = "default"
    ) -> None:
        """
        Update a document in Pinecone
        
        Args:
            id: Document ID
            document: Updated document with 'content' and 'metadata'
            collection: Collection name (namespace)
        """
        try:
            # Generate new embedding
            if isinstance(self.embedding_function, asyncio.coroutine):
                embedding = await self.embedding_function(document['content'])
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(
                    None,
                    self.embedding_function,
                    [document['content']]
                )
                embedding = embedding[0]
            
            # Prepare metadata
            metadata = document.get('metadata', {})
            metadata['content'] = document['content'][:1000]
            metadata['collection'] = collection
            
            # Update vector
            self.index.upsert(
                vectors=[{
                    'id': id,
                    'values': embedding,
                    'metadata': metadata
                }],
                namespace=collection
            )
            
            logger.info(f"Updated document {id} in Pinecone")
            
        except Exception as e:
            logger.error(f"Pinecone update error: {str(e)}")
            raise
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID from content"""
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats.total_vector_count,
                'dimension': stats.dimension,
                'namespaces': stats.namespaces
            }
        except Exception as e:
            logger.error(f"Pinecone stats error: {str(e)}")
            return {}