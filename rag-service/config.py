"""
Configuration Management for RAG Service
Handles environment variables and service settings
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Service Configuration
    SERVICE_NAME: str = "rag-service"
    SERVICE_PORT: int = 8002
    DEBUG: bool = False
    
    # Local Embedding Model (NO API CALLS - 100% FREE)
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Qdrant Configuration
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "aws_best_practices"
    
    # Embedding Configuration (Local model uses 384 dimensions)
    EMBEDDING_DIMENSION: int = 384
    
    # Search Configuration
    DEFAULT_SEARCH_RESULTS: int = 5
    MAX_SEARCH_RESULTS: int = 20
    
    # Document Configuration
    MAX_DOCUMENT_LENGTH: int = 10000
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Other Microservices URLs
    AI_SERVICE_URL: str = "http://ai-service:8001"
    MCP_SERVICE_URL: str = "http://mcp-service:8003"
    INFRA_SERVICE_URL: str = "http://infra-service:8004"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


# Document Categories
DOCUMENT_CATEGORIES = [
    "networking",
    "security",
    "compute",
    "storage",
    "database",
    "serverless",
    "containers",
    "cost",
    "management",
    "terraform",
    "monitoring",
    "compliance"
]


# AWS Resource Types
AWS_RESOURCE_TYPES = [
    "vpc",
    "subnet",
    "security_group",
    "nat_gateway",
    "internet_gateway",
    "route_table",
    "ec2",
    "alb",
    "nlb",
    "rds",
    "aurora",
    "dynamodb",
    "s3",
    "efs",
    "lambda",
    "api_gateway",
    "ecs",
    "eks",
    "ecr",
    "iam",
    "kms",
    "cloudwatch",
    "cloudfront",
    "route53",
    "sns",
    "sqs",
    "secrets_manager",
    "parameter_store"
]


# Importance Levels
IMPORTANCE_LEVELS = ["low", "medium", "high", "critical"]


# Default Metadata Template
DEFAULT_METADATA = {
    "source": "User Uploaded",
    "category": "general",
    "provider": "aws",
    "importance": "medium"
}
