"""
Infrastructure Template Store
Stores and searches pre-defined infrastructure templates in Qdrant
"""

import logging
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

logger = logging.getLogger(__name__)


class InfrastructureTemplateStore:
    """
    Store and search pre-defined infrastructure templates
    """
    
    def __init__(self, qdrant_client: QdrantClient, embedding_model: SentenceTransformer):
        self.client = qdrant_client
        self.model = embedding_model
        self.collection_name = "infrastructure_templates"
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        
        # Create collection if doesn't exist
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create Qdrant collection for templates"""
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
    
    def template_exists(self, template_id: str) -> bool:
        """Check if template already exists in collection"""
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {
                            "key": "template_id",
                            "match": {"value": template_id}
                        }
                    ]
                },
                limit=1
            )
            return len(results[0]) > 0
        except Exception as e:
            logger.error(f"Error checking template existence: {e}")
            return False
    
    def store_template(self, template: Dict) -> bool:
        """
        Store infrastructure template
        
        Args:
            template: Template dictionary with name, description, components, etc.
        """
        try:
            template_id = template.get("id")
            
            # Check if template already exists
            if self.template_exists(template_id):
                logger.info(f"Template already exists: {template.get('name')} (skipping)")
                return True
            
            # Generate text for embedding
            text_for_embedding = self._template_to_text(template)
            
            # Create embedding
            embedding = self.model.encode(text_for_embedding).tolist()
            
            # Create unique ID
            point_id = str(uuid.uuid4())
            
            # Store in Qdrant
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "template_id": template.get("id"),
                    "name": template.get("name"),
                    "description": template.get("description"),
                    "use_case": template.get("use_case"),
                    "components": template.get("components", []),
                    "services": template.get("services", {}),
                    "estimated_cost": template.get("estimated_cost"),
                    "complexity": template.get("complexity"),
                    "tags": template.get("tags", [])
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"✅ Stored NEW template: {template.get('name')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store template: {e}")
            return False
    
    def search_templates(
        self,
        user_requirement: str,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Search for matching infrastructure templates
        
        Args:
            user_requirement: User's infrastructure requirements
            top_k: Number of templates to return
        
        Returns:
            List of matching templates with similarity scores
        """
        try:
            # Create query vector
            query_vector = self.model.encode(user_requirement).tolist()
            
            # Search Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=0.3  # Lower threshold for templates
            )
            
            # Format results
            templates = []
            for result in results:
                templates.append({
                    "template_id": result.payload.get("template_id"),
                    "name": result.payload.get("name"),
                    "description": result.payload.get("description"),
                    "use_case": result.payload.get("use_case"),
                    "components": result.payload.get("components", []),
                    "services": result.payload.get("services", {}),
                    "estimated_cost": result.payload.get("estimated_cost"),
                    "complexity": result.payload.get("complexity"),
                    "tags": result.payload.get("tags", []),
                    "similarity_score": result.score
                })
            
            logger.info(f"Found {len(templates)} matching templates")
            return templates
            
        except Exception as e:
            logger.error(f"Failed to search templates: {e}")
            return []
    
    def get_all_templates(self) -> List[Dict]:
        """Get all stored templates"""
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                limit=100
            )
            
            templates = []
            for point in results[0]:
                templates.append({
                    "template_id": point.payload.get("template_id"),
                    "name": point.payload.get("name"),
                    "description": point.payload.get("description"),
                    "components": point.payload.get("components", []),
                    "tags": point.payload.get("tags", [])
                })
            
            return templates
            
        except Exception as e:
            logger.error(f"Failed to get templates: {e}")
            return []
    
    def _template_to_text(self, template: Dict) -> str:
        """Convert template to text for embedding"""
        text = f"""
{template.get('name', '')}
{template.get('description', '')}
{template.get('use_case', '')}

Components: {', '.join(template.get('components', []))}
Tags: {', '.join(template.get('tags', []))}
"""
        return text.strip()


def create_template_store(qdrant_client: QdrantClient, embedding_model: SentenceTransformer):
    """Factory function to create template store"""
    return InfrastructureTemplateStore(qdrant_client, embedding_model)