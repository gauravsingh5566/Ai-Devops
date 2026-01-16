"""
RAG Service Connection for Plan Validator
Provides Terraform examples to the validator
"""

import httpx
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class TerraformStoreClient:
    """
    Client to connect to RAG service for Terraform examples
    """
    
    def __init__(self, rag_service_url: str):
        self.rag_service_url = rag_service_url
    
    def search_similar_terraform(
        self,
        error_description: str,
        failed_code: str,
        resource_types: List[str],
        top_k: int = 3
    ) -> List[Dict]:
        """
        Search RAG service for similar working Terraform examples
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    f"{self.rag_service_url}/terraform/search",
                    json={
                        "error_description": error_description,
                        "failed_code": failed_code,
                        "resource_types": resource_types,
                        "top_k": top_k
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"RAG search failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.warning(f"Could not connect to RAG service: {e}")
            return []


def create_rag_client(rag_service_url: str):
    """Factory function to create RAG client"""
    return TerraformStoreClient(rag_service_url)