"""
Terraform Code Storage & Retrieval
Store successful Terraform deployments as vectors for reference
"""

import logging
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib
import json

logger = logging.getLogger(__name__)


class TerraformCodeStore:
    """
    Store and retrieve Terraform code examples using vector similarity
    """
    
    def __init__(self, qdrant_client: QdrantClient, embedding_model: SentenceTransformer):
        self.client = qdrant_client
        self.model = embedding_model
        self.collection_name = "terraform_examples"
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        
        # Create collection if doesn't exist
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create Qdrant collection for Terraform examples"""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection exists: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
    
    def store_successful_terraform(
        self, 
        terraform_code: str, 
        deployment_id: str,
        resource_types: List[str],
        description: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Store successful Terraform deployment for future reference
        
        Args:
            terraform_code: The working Terraform code
            deployment_id: Unique deployment identifier
            resource_types: List of AWS resources (e.g., ['aws_vpc', 'aws_subnet'])
            description: Human-readable description
            metadata: Additional metadata (region, cost, etc.)
        """
        try:
            # Generate embedding from code + description
            text_to_embed = f"{description}\n\nResources: {', '.join(resource_types)}\n\nCode:\n{terraform_code}"
            embedding = self.model.encode(text_to_embed).tolist()
            
            # Create unique ID using UUID (Qdrant requires UUID or integer)
            import uuid
            code_hash = hashlib.sha256(terraform_code.encode()).hexdigest()
            # Convert hash to UUID
            point_id = str(uuid.UUID(code_hash[:32]))
            
            # Store in Qdrant
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "terraform_code": terraform_code,
                    "deployment_id": deployment_id,
                    "resource_types": resource_types,
                    "description": description,
                    "metadata": metadata or {},
                    "code_hash": code_hash[:16]
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Stored Terraform example: {deployment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store Terraform code: {e}")
            return False
    
    def search_similar_terraform(
        self, 
        error_description: str,
        failed_code: str,
        resource_types: List[str],
        top_k: int = 3
    ) -> List[Dict]:
        """
        Search for similar working Terraform examples
        
        Args:
            error_description: Description of the error
            failed_code: The code that failed
            resource_types: Resources involved in the error
            top_k: Number of examples to return
        
        Returns:
            List of similar working Terraform examples
        """
        try:
            # Create search query
            search_text = f"Error: {error_description}\n\nResources: {', '.join(resource_types)}\n\nFailed code:\n{failed_code}"
            query_vector = self.model.encode(search_text).tolist()
            
            # Search Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=0.5  # Only return similar examples
            )
            
            # Format results
            examples = []
            for result in results:
                examples.append({
                    "terraform_code": result.payload["terraform_code"],
                    "description": result.payload["description"],
                    "resource_types": result.payload["resource_types"],
                    "similarity_score": result.score,
                    "deployment_id": result.payload["deployment_id"],
                    "metadata": result.payload.get("metadata", {})
                })
            
            logger.info(f"Found {len(examples)} similar Terraform examples")
            return examples
            
        except Exception as e:
            logger.error(f"Failed to search Terraform examples: {e}")
            return []
    
    def search_by_resource_type(
        self, 
        resource_type: str, 
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search for examples of specific resource type
        
        Args:
            resource_type: AWS resource type (e.g., 'aws_vpc')
            top_k: Number of examples to return
        """
        try:
            # Search by resource type
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {
                            "key": "resource_types",
                            "match": {"value": resource_type}
                        }
                    ]
                },
                limit=top_k
            )
            
            examples = []
            for point in results[0]:
                examples.append({
                    "terraform_code": point.payload["terraform_code"],
                    "description": point.payload["description"],
                    "resource_types": point.payload["resource_types"],
                    "deployment_id": point.payload["deployment_id"]
                })
            
            logger.info(f"Found {len(examples)} examples for {resource_type}")
            return examples
            
        except Exception as e:
            logger.error(f"Failed to search by resource type: {e}")
            return []


def create_terraform_store(qdrant_client: QdrantClient, embedding_model: SentenceTransformer):
    """Factory function to create Terraform code store"""
    return TerraformCodeStore(qdrant_client, embedding_model)