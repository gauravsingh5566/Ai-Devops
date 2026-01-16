"""
Pre-defined AWS Infrastructure Templates
These will be stored in Qdrant for intelligent template matching
"""

INFRASTRUCTURE_TEMPLATES = [
    {
        "id": "microservices-arch",
        "name": "Microservices Architecture with Database",
        "description": "Complete microservices setup with load balancing, auto-scaling, and RDS database",
        "use_case": "Deploy multiple microservices with central database, API gateway, and load balancing",
        "components": [
            "VPC with public and private subnets",
            "Application Load Balancer (ALB)",
            "ECS Fargate for containerized microservices",
            "Auto Scaling Groups",
            "RDS (PostgreSQL/MySQL) Multi-AZ",
            "ElastiCache Redis for caching",
            "CloudWatch for monitoring",
            "Security Groups for network isolation",
            "NAT Gateway for private subnet internet access"
        ],
        "services": {
            "compute": ["ECS Fargate", "Auto Scaling"],
            "networking": ["VPC", "ALB", "NAT Gateway"],
            "database": ["RDS Multi-AZ", "ElastiCache Redis"],
            "monitoring": ["CloudWatch", "CloudWatch Logs"],
            "security": ["Security Groups", "IAM Roles"]
        },
        "estimated_cost": "$300-500/month",
        "complexity": "medium",
        "tags": ["microservices", "containers", "database", "scalable", "production-ready"]
    },
    
    {
        "id": "web-app-3tier",
        "name": "Three-Tier Web Application",
        "description": "Classic web application with presentation, application, and data layers",
        "use_case": "Traditional web applications with frontend, backend API, and database",
        "components": [
            "VPC with multi-AZ subnets",
            "Application Load Balancer",
            "EC2 instances for application servers",
            "Auto Scaling for high availability",
            "RDS database (MySQL/PostgreSQL)",
            "S3 for static assets",
            "CloudFront CDN",
            "Route53 for DNS",
            "ElastiCache for session management",
            "Security Groups and NACLs"
        ],
        "services": {
            "compute": ["EC2", "Auto Scaling"],
            "networking": ["VPC", "ALB", "CloudFront"],
            "storage": ["S3", "EBS"],
            "database": ["RDS", "ElastiCache"],
            "dns": ["Route53"],
            "monitoring": ["CloudWatch"]
        },
        "estimated_cost": "$200-400/month",
        "complexity": "low-medium",
        "tags": ["web-app", "three-tier", "traditional", "scalable", "cdn"]
    },
    
    {
        "id": "data-pipeline",
        "name": "Data Processing Pipeline",
        "description": "ETL pipeline for data ingestion, processing, and analytics",
        "use_case": "Process large volumes of data, run analytics, and generate insights",
        "components": [
            "S3 for data lake storage",
            "Lambda for serverless processing",
            "Kinesis for real-time data streaming",
            "Glue for ETL jobs",
            "Redshift for data warehousing",
            "Athena for querying S3 data",
            "Step Functions for workflow orchestration",
            "EventBridge for event-driven triggers",
            "CloudWatch for monitoring",
            "IAM roles for service permissions"
        ],
        "services": {
            "storage": ["S3"],
            "compute": ["Lambda", "Glue"],
            "streaming": ["Kinesis Data Streams"],
            "analytics": ["Athena", "Redshift"],
            "orchestration": ["Step Functions", "EventBridge"],
            "monitoring": ["CloudWatch"]
        },
        "estimated_cost": "$150-300/month",
        "complexity": "medium-high",
        "tags": ["data-pipeline", "etl", "analytics", "serverless", "big-data"]
    },
    
    {
        "id": "serverless-api",
        "name": "Serverless API Backend",
        "description": "Fully serverless API with authentication and database",
        "use_case": "Build scalable APIs without managing servers",
        "components": [
            "API Gateway for REST/HTTP APIs",
            "Lambda functions for business logic",
            "DynamoDB for NoSQL database",
            "Cognito for user authentication",
            "S3 for file storage",
            "CloudFront for API caching",
            "CloudWatch Logs",
            "IAM roles and policies",
            "Secrets Manager for credentials",
            "SQS for async processing"
        ],
        "services": {
            "api": ["API Gateway"],
            "compute": ["Lambda"],
            "database": ["DynamoDB"],
            "auth": ["Cognito"],
            "storage": ["S3"],
            "cdn": ["CloudFront"],
            "queue": ["SQS"],
            "monitoring": ["CloudWatch"]
        },
        "estimated_cost": "$50-150/month",
        "complexity": "low",
        "tags": ["serverless", "api", "lambda", "dynamodb", "cost-effective"]
    },
    
    {
        "id": "ml-training-inference",
        "name": "Machine Learning Training & Inference",
        "description": "Complete ML infrastructure for training models and serving predictions",
        "use_case": "Train machine learning models and deploy them for real-time inference",
        "components": [
            "SageMaker for training and hosting",
            "S3 for training data and model artifacts",
            "EC2 GPU instances for training",
            "Lambda for preprocessing",
            "API Gateway for inference endpoint",
            "DynamoDB for feature store",
            "CloudWatch for model monitoring",
            "Step Functions for ML workflows",
            "ECR for container images",
            "IAM roles for permissions"
        ],
        "services": {
            "ml": ["SageMaker", "SageMaker Endpoints"],
            "compute": ["EC2 GPU", "Lambda"],
            "storage": ["S3", "ECR"],
            "database": ["DynamoDB"],
            "api": ["API Gateway"],
            "orchestration": ["Step Functions"],
            "monitoring": ["CloudWatch", "SageMaker Model Monitor"]
        },
        "estimated_cost": "$400-800/month",
        "complexity": "high",
        "tags": ["machine-learning", "ai", "sagemaker", "gpu", "inference"]
    }
]


def get_template_text_for_embedding(template: dict) -> str:
    """
    Convert template to text format for vector embedding
    """
    text = f"""
Template: {template['name']}
Description: {template['description']}
Use Case: {template['use_case']}

Components:
{chr(10).join([f"- {comp}" for comp in template['components']])}

Services:
{chr(10).join([f"{category}: {', '.join(services)}" for category, services in template['services'].items()])}

Tags: {', '.join(template['tags'])}
Complexity: {template['complexity']}
Cost: {template['estimated_cost']}
"""
    return text.strip()