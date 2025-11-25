"""
Configuration Management for AI Service
Handles environment variables and service settings
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Service Configuration
    SERVICE_NAME: str = "ai-service"
    SERVICE_PORT: int = 8001
    DEBUG: bool = False
    
    # Claude AI Configuration
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    MAX_TOKENS: int = 4000
    
    # Other Microservices URLs
    RAG_SERVICE_URL: str = "http://rag-service:8002"
    MCP_SERVICE_URL: str = "http://mcp-service:8003"
    INFRA_SERVICE_URL: str = "http://infra-service:8004"
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    
    # Timeouts
    REQUEST_TIMEOUT: int = 30
    CLAUDE_API_TIMEOUT: int = 60
    
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


# Prompt Templates
INTENT_PARSING_PROMPT = """You are an AWS infrastructure expert. Parse this user request into structured JSON.

User Request: "{user_message}"

Extract and return ONLY a JSON object with this exact structure:
{{
    "resources": ["list of AWS resources needed"],
    "requirements": {{
        "key": "value pairs of specific requirements"
    }},
    "estimated_complexity": "simple|moderate|complex",
    "needs_rag": true|false
}}

Rules:
- Identify all AWS resources (vpc, subnet, ec2, rds, etc.)
- Extract specific requirements (CIDR blocks, instance types, etc.)
- Determine if we need to search best practices (needs_rag)
- Keep it concise and accurate

Return only valid JSON, no markdown or explanation."""


CODE_GENERATION_PROMPT = """You are a senior DevOps engineer generating production-ready Terraform code.

INFRASTRUCTURE REQUIREMENTS:
{intent}

{rag_context}

{policies}

Generate Terraform code following these guidelines:
1. Use latest AWS provider syntax
2. Include proper resource naming with tags
3. Add security best practices (security groups, encryption)
4. Include output blocks for important values
5. Add comments explaining key decisions
6. Use variables for reusable values
7. Follow AWS Well-Architected Framework

Return a JSON object with this structure:
{{
    "terraform_code": "complete Terraform code here",
    "explanation": "brief explanation of what this creates",
    "resources_created": ["list of AWS resources"],
    "estimated_cost_info": "rough monthly cost estimate and key cost drivers"
}}

Make the code production-ready, secure, and well-documented. Return only valid JSON."""


CODE_REFINEMENT_PROMPT = """You are refining Terraform code based on feedback.

ORIGINAL CODE:
```terraform
{original_code}
```

FEEDBACK/ISSUES:
{feedback}

VALIDATION RESULTS:
{validation_results}

Please refine the code to address the feedback while maintaining functionality.
Return improved Terraform code that fixes the issues mentioned.

Return a JSON object:
{{
    "refined_code": "improved Terraform code",
    "changes_made": "list of what was changed and why",
    "remaining_concerns": "any issues that couldn't be fully addressed"
}}"""


# AWS Resource Mapping
AWS_RESOURCE_KEYWORDS = {
    "vpc": ["vpc", "virtual private cloud", "network"],
    "subnet": ["subnet", "subnetwork"],
    "ec2": ["ec2", "instance", "server", "virtual machine", "vm"],
    "rds": ["rds", "database", "db", "mysql", "postgres"],
    "s3": ["s3", "bucket", "storage"],
    "lambda": ["lambda", "function", "serverless"],
    "alb": ["alb", "load balancer", "application load balancer"],
    "ecs": ["ecs", "container", "docker"],
    "eks": ["eks", "kubernetes", "k8s"],
    "cloudfront": ["cloudfront", "cdn"],
    "route53": ["route53", "dns", "domain"],
    "iam": ["iam", "role", "policy", "permission"],
    "security_group": ["security group", "firewall", "sg"],
    "nat_gateway": ["nat", "nat gateway"],
    "internet_gateway": ["igw", "internet gateway"]
}


# Complexity Estimation Rules
COMPLEXITY_RULES = {
    "simple": {
        "max_resources": 3,
        "keywords": ["single", "basic", "simple", "small"]
    },
    "moderate": {
        "max_resources": 10,
        "keywords": ["multi", "tier", "environment"]
    },
    "complex": {
        "max_resources": 999,
        "keywords": ["enterprise", "production", "high availability", "multi-region"]
    }
}