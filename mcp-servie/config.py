"""
Configuration Management for MCP Service
Handles environment variables and service settings
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Service Configuration
    SERVICE_NAME: str = "mcp-service"
    SERVICE_PORT: int = 8003
    DEBUG: bool = False
    
    # AWS Configuration (for future AWS API integration)
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # Validation Settings
    DEFAULT_VALIDATION_LEVEL: str = "standard"
    MAX_COST_THRESHOLD: float = 1000.0  # USD per month
    
    # Security Settings
    ENFORCE_ENCRYPTION: bool = True
    ALLOW_PUBLIC_ACCESS: bool = False
    MIN_SECURITY_SCORE: int = 70
    
    # Quota Settings
    QUOTA_WARNING_THRESHOLD: float = 0.8  # 80% of limit
    
    # Other Microservices URLs
    AI_SERVICE_URL: str = "http://ai-service:8001"
    RAG_SERVICE_URL: str = "http://rag-service:8002"
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


# Security Rule Definitions
SECURITY_RULES = {
    "SEC001": {
        "name": "Encryption at Rest",
        "severity": "high",
        "description": "Data stores must have encryption enabled",
        "affected_resources": ["aws_ebs_volume", "aws_rds_instance", "aws_s3_bucket"]
    },
    "SEC002": {
        "name": "Public Access Prevention",
        "severity": "critical",
        "description": "Security groups should not allow unrestricted access (0.0.0.0/0)",
        "affected_resources": ["aws_security_group"]
    },
    "SEC003": {
        "name": "S3 Bucket Security",
        "severity": "critical",
        "description": "S3 buckets should not have public ACLs",
        "affected_resources": ["aws_s3_bucket"]
    },
    "SEC004": {
        "name": "IAM Least Privilege",
        "severity": "medium",
        "description": "IAM policies should avoid wildcard permissions",
        "affected_resources": ["aws_iam_policy", "aws_iam_role_policy"]
    },
    "SEC005": {
        "name": "RDS Public Access",
        "severity": "high",
        "description": "RDS instances should not be publicly accessible",
        "affected_resources": ["aws_db_instance"]
    }
}


# Cost optimization recommendations
COST_RECOMMENDATIONS = {
    "high_cost": "Consider using Reserved Instances or Savings Plans for predictable workloads",
    "oversized_instance": "Instance type may be oversized. Start smaller and scale based on metrics",
    "unused_resources": "Remove unused resources like unattached EBS volumes or idle load balancers",
    "data_transfer": "Minimize cross-AZ and inter-region data transfer costs",
    "storage_optimization": "Use lifecycle policies for S3 and consider EBS volume types"
}


# Resource naming conventions
NAMING_CONVENTIONS = {
    "pattern": r"^[a-z][a-z0-9-]*[a-z0-9]$",
    "max_length": 63,
    "allowed_chars": "lowercase letters, numbers, hyphens",
    "rules": [
        "Must start with a letter",
        "Must end with a letter or number",
        "Can only contain lowercase letters, numbers, and hyphens",
        "No consecutive hyphens"
    ]
}


# Tagging requirements
REQUIRED_TAGS = [
    "Name",
    "Environment",
    "Owner",
    "CostCenter",
    "Project"
]
