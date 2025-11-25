"""
AI Service - Natural Language Processing & Code Generation
Handles user intent parsing and Terraform code generation using Claude AI
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import anthropic
import os
from datetime import datetime

# Custom OpenAPI schema for better Swagger documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="🧠 AI Service - DevOps Assistant",
        version="1.0.0",
        description="""
## AI-Powered Infrastructure Code Generation

This service uses **Claude AI** to convert natural language infrastructure requests 
into production-ready Terraform code.

### 🎯 Key Features

- **Intent Parsing**: Convert natural language to structured requirements
- **Code Generation**: Generate production-ready Terraform with best practices
- **Code Refinement**: Improve code based on validation feedback

### 🔄 Typical Workflow

1. User sends natural language request → `/parse-intent`
2. Get best practices from RAG service (if needed)
3. Generate Terraform code → `/generate-code`
4. Validate with MCP service
5. Refine if issues found → `/refine-code`

### 🔑 Authentication

Set your Anthropic API key as environment variable:
```bash
export ANTHROPIC_API_KEY=your-key-here
```

### 📚 Related Services

- **RAG Service** (Port 8002): Knowledge base and best practices
- **MCP Service** (Port 8003): Cost, security, and quota validation
- **Infrastructure Service** (Port 8004): Terraform deployment
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Intent Processing",
                "description": "Parse natural language into structured infrastructure requirements"
            },
            {
                "name": "Code Generation",
                "description": "Generate and refine Terraform infrastructure code"
            },
            {
                "name": "Health & Status",
                "description": "Service health checks and status monitoring"
            }
        ]
    )
    
    # Add custom logo and styling
    openapi_schema["info"]["x-logo"] = {
        "url": "https://www.terraform.io/img/logo-hashicorp.svg"
    }
    
    # Add contact info
    openapi_schema["info"]["contact"] = {
        "name": "AI DevOps Assistant",
        "url": "https://github.com/your-repo/ai-devops-assistant",
        "email": "support@example.com"
    }
    
    # Add license
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title="AI Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Set custom OpenAPI schema
app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Claude AI client
claude_client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY", "your-api-key-here")
)


class UserRequest(BaseModel):
    """User's natural language infrastructure request"""
    message: str = Field(
        ...,
        description="Natural language description of the infrastructure you want to create",
        example="Create a VPC with 2 private subnets in us-east-1 region",
        min_length=5,
        max_length=2000
    )
    context: Optional[Dict] = Field(
        default=None,
        description="Additional context for the request (region, environment, etc.)",
        example={"region": "us-east-1", "environment": "production"}
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Create a 3-tier application with load balancer, auto-scaling EC2 instances, and RDS database",
                "context": {
                    "region": "us-east-1",
                    "environment": "production",
                    "team": "platform"
                }
            }
        }


class IntentResponse(BaseModel):
    """Parsed infrastructure intent"""
    resources: List[str] = Field(
        ...,
        description="List of AWS resources identified in the request",
        example=["vpc", "subnet", "nat_gateway", "route_table"]
    )
    requirements: Dict = Field(
        ...,
        description="Specific requirements extracted from the request",
        example={"vpc_count": 1, "subnet_count": 2, "subnet_type": "private"}
    )
    estimated_complexity: str = Field(
        ...,
        description="Estimated complexity level: simple, moderate, or complex",
        example="simple"
    )
    needs_rag: bool = Field(
        ...,
        description="Whether this request needs best practices from RAG service",
        example=True
    )

    class Config:
        json_schema_extra = {
            "example": {
                "resources": ["vpc", "subnet", "nat_gateway", "internet_gateway", "route_table"],
                "requirements": {
                    "vpc_count": 1,
                    "subnet_count": 2,
                    "subnet_type": "private",
                    "region": "us-east-1",
                    "high_availability": True
                },
                "estimated_complexity": "moderate",
                "needs_rag": True
            }
        }


class CodeGenerationRequest(BaseModel):
    """Request for Terraform code generation"""
    intent: Dict = Field(
        ...,
        description="Parsed intent from /parse-intent endpoint",
        example={
            "resources": ["vpc", "subnet"],
            "requirements": {"vpc_count": 1, "subnet_count": 2}
        }
    )
    rag_context: Optional[List[Dict]] = Field(
        default=None,
        description="Best practices and templates from RAG service",
        example=[
            {"content": "VPC Best Practice: Use /16 CIDR for production VPCs", "score": 0.95}
        ]
    )
    organization_policies: Optional[Dict] = Field(
        default=None,
        description="Organization-specific policies and requirements",
        example={
            "tagging": "All resources must have Environment and Team tags",
            "encryption": "All data must be encrypted at rest"
        }
    )

    class Config:
        json_schema_extra = {
            "example": {
                "intent": {
                    "resources": ["vpc", "subnet", "nat_gateway"],
                    "requirements": {
                        "vpc_count": 1,
                        "subnet_count": 2,
                        "subnet_type": "private",
                        "region": "us-east-1"
                    }
                },
                "rag_context": [
                    {
                        "content": "VPC Best Practice: Use /16 CIDR block for VPCs to allow room for growth",
                        "metadata": {"source": "AWS Well-Architected Framework"},
                        "score": 0.95
                    },
                    {
                        "content": "Always deploy NAT Gateways in multiple AZs for high availability",
                        "metadata": {"source": "AWS Documentation"},
                        "score": 0.88
                    }
                ],
                "organization_policies": {
                    "tagging": "All resources must have Environment, Team, and CostCenter tags",
                    "encryption": "Enable encryption at rest for all storage resources",
                    "naming": "Use format: {env}-{team}-{resource}-{number}"
                }
            }
        }


class CodeGenerationResponse(BaseModel):
    """Generated Terraform code with metadata"""
    terraform_code: str = Field(
        ...,
        description="Complete, production-ready Terraform code"
    )
    explanation: str = Field(
        ...,
        description="Human-readable explanation of what the code creates",
        example="Creates a VPC with 2 private subnets across different AZs for high availability"
    )
    resources_created: List[str] = Field(
        ...,
        description="List of AWS resources that will be created",
        example=["aws_vpc", "aws_subnet", "aws_nat_gateway", "aws_route_table"]
    )
    estimated_cost_info: str = Field(
        ...,
        description="Rough monthly cost estimate and key cost drivers",
        example="$45/month - NAT Gateway $32, EIP $3.60, VPC free tier"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "terraform_code": '''# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name        = "production-main-vpc"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

# Private Subnet 1
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  
  tags = {
    Name        = "production-private-subnet-1"
    Environment = "production"
  }
}

# Private Subnet 2
resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
  
  tags = {
    Name        = "production-private-subnet-2"
    Environment = "production"
  }
}''',
                "explanation": "Creates a production VPC with /16 CIDR block and 2 private subnets distributed across us-east-1a and us-east-1b availability zones for high availability. Includes proper tagging and DNS support enabled.",
                "resources_created": [
                    "aws_vpc.main",
                    "aws_subnet.private_1",
                    "aws_subnet.private_2"
                ],
                "estimated_cost_info": "$0/month - VPC and subnets are free. Add NAT Gateway for internet access (~$32/month per AZ)."
            }
        }


class CodeRefinementRequest(BaseModel):
    """Request to refine Terraform code based on feedback"""
    original_code: str = Field(
        ...,
        description="The original Terraform code to be refined",
        min_length=10
    )
    feedback: str = Field(
        ...,
        description="Feedback or issues that need to be addressed",
        example="Cost too high - use smaller instance types. Add encryption to EBS volumes."
    )
    validation_results: Optional[Dict] = Field(
        default=None,
        description="Results from MCP validation service",
        example={
            "monthly_cost": 250,
            "security_issues": ["EBS volumes not encrypted"],
            "quota_warnings": []
        }
    )

    class Config:
        json_schema_extra = {
            "example": {
                "original_code": '''resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.2xlarge"
  
  tags = {
    Name = "app-server"
  }
}''',
                "feedback": "Instance type t3.2xlarge is too expensive for development. Use t3.small instead. Also add EBS encryption.",
                "validation_results": {
                    "monthly_cost": 245.50,
                    "cost_breakdown": {
                        "ec2": 240,
                        "ebs": 5.50
                    },
                    "security_issues": [
                        "EBS root volume is not encrypted",
                        "No security group specified"
                    ],
                    "recommendations": [
                        "Consider t3.small for development ($15/month)",
                        "Enable EBS encryption with AWS managed key"
                    ]
                }
            }
        }


class CodeRefinementResponse(BaseModel):
    """Refined Terraform code with change documentation"""
    refined_code: str = Field(
        ...,
        description="Improved Terraform code addressing the feedback"
    )
    changes_made: str = Field(
        ...,
        description="Summary of changes made to address feedback",
        example="Changed instance type from t3.2xlarge to t3.small. Added EBS encryption."
    )
    remaining_concerns: str = Field(
        ...,
        description="Any issues that couldn't be fully addressed",
        example="None - all issues resolved"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "refined_code": '''resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.small"
  
  root_block_device {
    volume_size = 20
    encrypted   = true
  }
  
  tags = {
    Name        = "app-server"
    Environment = "development"
  }
}''',
                "changes_made": "1. Changed instance_type from t3.2xlarge to t3.small (cost reduced from $240/month to $15/month). 2. Added root_block_device with encryption enabled. 3. Added Environment tag.",
                "remaining_concerns": "Consider adding a security group to restrict inbound traffic. VPC placement not specified - will use default VPC."
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(
        ...,
        description="Service health status",
        example="healthy"
    )
    claude_api: str = Field(
        ...,
        description="Claude API connection status",
        example="connected"
    )
    timestamp: str = Field(
        ...,
        description="Timestamp of health check",
        example="2025-11-13T10:30:00.000000"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if service is degraded"
    )


@app.get(
    "/",
    tags=["Health & Status"],
    summary="Service Status",
    description="Quick health check to verify the service is running"
)
async def root():
    """
    Quick health check endpoint.
    
    Returns basic service information to confirm the AI Service is operational.
    For detailed health status including Claude API connectivity, use `/health`.
    """
    return {
        "service": "AI Service",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post(
    "/parse-intent",
    response_model=IntentResponse,
    tags=["Intent Processing"],
    summary="Parse Natural Language to Infrastructure Intent",
    description="""
Convert a natural language infrastructure request into structured JSON that can be 
used for code generation.

### What it does:
1. Analyzes the user's request using Claude AI
2. Identifies required AWS resources (VPC, EC2, RDS, etc.)
3. Extracts specific requirements (CIDR blocks, instance types, etc.)
4. Estimates complexity (simple/moderate/complex)
5. Determines if RAG context is needed

### Example Requests:
- "Create a VPC with 2 private subnets"
- "Deploy a 3-tier web application with load balancer"
- "Set up an EKS cluster with 3 worker nodes"
""",
    responses={
        200: {
            "description": "Successfully parsed intent",
            "content": {
                "application/json": {
                    "example": {
                        "resources": ["vpc", "subnet", "nat_gateway"],
                        "requirements": {
                            "vpc_count": 1,
                            "subnet_count": 2,
                            "subnet_type": "private"
                        },
                        "estimated_complexity": "simple",
                        "needs_rag": True
                    }
                }
            }
        },
        500: {
            "description": "Intent parsing failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Intent parsing failed: Claude API error"
                    }
                }
            }
        }
    }
)
async def parse_intent(request: UserRequest):
    """
    Parse user's natural language request into structured infrastructure intent.
    
    This endpoint uses Claude AI to understand and extract:
    - AWS resources needed
    - Specific requirements and configurations
    - Complexity estimation
    - Whether best practices lookup is needed
    
    **Example:**
    ```
    Input: "Create VPC with 2 subnets"
    Output: {
        "resources": ["vpc", "subnet"],
        "requirements": {"vpc_count": 1, "subnet_count": 2},
        "estimated_complexity": "simple",
        "needs_rag": true
    }
    ```
    """
    try:
        prompt = f"""You are an AWS infrastructure expert. Parse this user request into structured JSON.

User Request: "{request.message}"

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

        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract JSON from response
        response_text = message.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        response_text = response_text.strip()
        
        # Parse JSON
        import json
        intent_data = json.loads(response_text)
        
        return IntentResponse(**intent_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent parsing failed: {str(e)}")


@app.post(
    "/generate-code",
    response_model=CodeGenerationResponse,
    tags=["Code Generation"],
    summary="Generate Terraform Code from Intent",
    description="""
Generate production-ready Terraform code based on parsed intent and optional context.

### What it does:
1. Takes the structured intent from `/parse-intent`
2. Incorporates best practices from RAG service (if provided)
3. Applies organization policies (if provided)
4. Generates complete Terraform code using Claude AI
5. Returns code with explanation and cost estimate

### Features included:
- ✅ Latest AWS provider syntax
- ✅ Proper resource naming with tags
- ✅ Security best practices
- ✅ Output blocks for important values
- ✅ Comments explaining key decisions
- ✅ Variables for reusable values
- ✅ AWS Well-Architected Framework compliance

### Typical Flow:
```
parse-intent → (optional) RAG service → generate-code → MCP validation
```
""",
    responses={
        200: {
            "description": "Successfully generated Terraform code"
        },
        500: {
            "description": "Code generation failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Code generation failed: Invalid intent structure"
                    }
                }
            }
        }
    }
)
async def generate_terraform_code(request: CodeGenerationRequest):
    """
    Generate production-ready Terraform code based on parsed intent and RAG context.
    
    This endpoint uses Claude AI to generate complete, deployable Terraform
    configurations that follow AWS best practices and organization policies.
    
    **Inputs:**
    - `intent`: Parsed requirements from `/parse-intent`
    - `rag_context`: Best practices from RAG service (optional)
    - `organization_policies`: Company-specific rules (optional)
    
    **Outputs:**
    - Complete Terraform code
    - Human-readable explanation
    - List of resources created
    - Cost estimate
    """
    try:
        # Build context from RAG results
        rag_context_text = ""
        if request.rag_context:
            rag_context_text = "\n\n=== BEST PRACTICES FROM KNOWLEDGE BASE ===\n"
            for idx, doc in enumerate(request.rag_context, 1):
                rag_context_text += f"\n{idx}. {doc.get('content', '')}\n"
        
        # Build policy context
        policy_text = ""
        if request.organization_policies:
            policy_text = f"\n\n=== ORGANIZATION POLICIES ===\n{request.organization_policies}\n"
        
        prompt = f"""You are a senior DevOps engineer generating production-ready Terraform code.

INFRASTRUCTURE REQUIREMENTS:
{request.intent}

{rag_context_text}
{policy_text}

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

        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Clean up markdown if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        response_text = response_text.strip()
        
        # Parse JSON response
        import json
        code_data = json.loads(response_text)
        
        return CodeGenerationResponse(**code_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Code generation failed: {str(e)}"
        )


@app.post(
    "/refine-code",
    response_model=CodeRefinementResponse,
    tags=["Code Generation"],
    summary="Refine Terraform Code Based on Feedback",
    description="""
Improve existing Terraform code based on validation feedback or user requests.

### When to use:
- MCP service found cost issues → optimize resources
- Security vulnerabilities detected → add encryption, tighten rules
- Quota limits exceeded → suggest alternatives
- User wants modifications → apply changes

### What it does:
1. Analyzes the original code and feedback
2. Uses Claude AI to understand required changes
3. Generates improved code addressing all issues
4. Documents what was changed and why
5. Notes any remaining concerns

### Example Use Cases:
- "Cost too high" → Switch to smaller instance types
- "Security issues" → Add encryption, security groups
- "Missing tags" → Add required tags
- "Wrong region" → Update region and AZs
""",
    responses={
        200: {
            "description": "Successfully refined code"
        },
        500: {
            "description": "Code refinement failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Code refinement failed: Unable to parse original code"
                    }
                }
            }
        }
    }
)
async def refine_terraform_code(request: CodeRefinementRequest):
    """
    Refine Terraform code based on user feedback or validation failures.
    
    Used when MCP service finds issues (cost too high, security problems, etc.)
    or when the user wants modifications to the generated code.
    
    **Example:**
    ```
    Input: Code with t3.2xlarge + "Cost too high"
    Output: Code with t3.small + documentation of changes
    ```
    """
    try:
        prompt = f"""You are refining Terraform code based on feedback.

ORIGINAL CODE:
```terraform
{request.original_code}
```

FEEDBACK/ISSUES:
{request.feedback}

VALIDATION RESULTS:
{request.validation_results if request.validation_results else "None provided"}

Please refine the code to address the feedback while maintaining functionality.
Return improved Terraform code that fixes the issues mentioned.

Return a JSON object:
{{
    "refined_code": "improved Terraform code",
    "changes_made": "list of what was changed and why",
    "remaining_concerns": "any issues that couldn't be fully addressed"
}}
"""

        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        import json
        result = json.loads(response_text.strip())
        
        return CodeRefinementResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code refinement failed: {str(e)}")


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health & Status"],
    summary="Detailed Health Check",
    description="""
Comprehensive health check including Claude API connectivity status.

### What it checks:
- Service is running
- Claude AI API is accessible
- API key is valid

### Response Status:
- `healthy`: All systems operational
- `degraded`: Service running but Claude API has issues

### Use Cases:
- Kubernetes liveness/readiness probes
- Monitoring and alerting
- Load balancer health checks
""",
    responses={
        200: {
            "description": "Health check completed",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "Service is healthy",
                            "value": {
                                "status": "healthy",
                                "claude_api": "connected",
                                "timestamp": "2025-11-13T10:30:00.000000"
                            }
                        },
                        "degraded": {
                            "summary": "Service is degraded",
                            "value": {
                                "status": "degraded",
                                "claude_api": "error",
                                "error": "API key invalid",
                                "timestamp": "2025-11-13T10:30:00.000000"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def health_check():
    """
    Detailed health check with Claude API status.
    
    Tests connectivity to Claude AI API by sending a minimal request.
    Returns service status, API connectivity, and timestamp.
    """
    try:
        # Quick test of Claude API
        test_message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )
        
        return HealthResponse(
            status="healthy",
            claude_api="connected",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            claude_api="error",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)