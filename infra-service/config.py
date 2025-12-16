"""
Configuration Management for Infrastructure Service
Handles environment variables and service settings
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Service Configuration
    SERVICE_NAME: str = "infra-service"
    SERVICE_PORT: int = 8004
    DEBUG: bool = False
    
    # Terraform Configuration
    TERRAFORM_VERSION: str = "1.6.0"
    WORKSPACE_DIR: str = "/app/workspaces"
    STATE_BACKEND: str = "local"  # local, s3, terraform-cloud
    
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # Deployment Settings
    DEFAULT_AUTO_APPROVE: bool = True
    MAX_CONCURRENT_DEPLOYMENTS: int = 5
    DEPLOYMENT_TIMEOUT: int = 300  # seconds
    
    # State Management
    S3_STATE_BUCKET: Optional[str] = None
    S3_STATE_KEY_PREFIX: str = "terraform-state"
    DYNAMODB_LOCK_TABLE: Optional[str] = None
    
    # Other Microservices URLs
    AI_SERVICE_URL: str = "http://ai-service:8001"
    RAG_SERVICE_URL: str = "http://rag-service:8002"
    MCP_SERVICE_URL: str = "http://mcp-service:8003"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    SAVE_TERRAFORM_LOGS: bool = True
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


# Deployment Status Definitions
DEPLOYMENT_STATUSES = {
    "pending": "Deployment created, awaiting initialization",
    "initializing": "Running terraform init",
    "initialized": "Terraform initialized successfully",
    "planning": "Generating execution plan",
    "planned": "Plan generated, ready to apply",
    "applying": "Creating infrastructure",
    "completed": "Deployment successful",
    "destroying": "Tearing down resources",
    "destroyed": "Resources destroyed",
    "failed": "Deployment failed",
    "cancelled": "Deployment cancelled by user"
}


# Terraform Command Templates
TERRAFORM_COMMANDS = {
    "init": ["terraform", "init", "-no-color"],
    "validate": ["terraform", "validate", "-no-color"],
    "plan": ["terraform", "plan", "-out=tfplan", "-no-color"],
    "apply": ["terraform", "apply", "-auto-approve", "-no-color"],
    "apply_plan": ["terraform", "apply", "-auto-approve", "tfplan"],
    "destroy": ["terraform", "destroy", "-auto-approve", "-no-color"],
    "output": ["terraform", "output", "-json"],
    "show": ["terraform", "show", "-no-color"],
    "state_list": ["terraform", "state", "list"]
}


# Default Terraform Provider Configuration
DEFAULT_PROVIDER_CONFIG = '''terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "{region}"
}
'''


# Backend Configuration Templates
BACKEND_CONFIGS = {
    "s3": '''terraform {
  backend "s3" {
    bucket         = "{bucket}"
    key            = "{key}"
    region         = "{region}"
    dynamodb_table = "{lock_table}"
    encrypt        = true
  }
}
''',
    "local": '''terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}
'''
}
