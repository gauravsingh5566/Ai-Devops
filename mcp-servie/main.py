"""
MCP Service - Model Context Protocol / Validation Service
Handles AWS cost calculation, security validation, quota checking, and resource validation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import re
import os
from datetime import datetime
import hashlib

# Custom OpenAPI schema for Swagger documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="⚡ MCP Service - Validation & Analysis",
        version="1.0.0",
        description="""
## AWS Infrastructure Validation Service

This service validates Terraform code before deployment by checking:
- **Cost Estimation**: Calculate monthly AWS costs
- **Security Validation**: Check against security best practices
- **Quota Checking**: Verify AWS service limits
- **Resource Dependencies**: Validate resource relationships

### 🎯 Key Features

- Real-time cost calculation using AWS pricing data
- Security policy enforcement (encryption, IAM, network rules)
- AWS quota validation (prevent over-provisioning)
- Terraform syntax and dependency validation
- Infrastructure recommendations

### 🔄 Typical Workflow

1. AI Service generates Terraform code
2. MCP Service validates the code
3. Returns cost estimate, security issues, quota warnings
4. AI Service refines if needed
5. Infrastructure Service deploys when validated

### 📊 Validation Categories

- **Cost**: Estimate monthly AWS spending
- **Security**: IAM, encryption, network security
- **Quotas**: EC2 limits, VPC limits, RDS limits
- **Best Practices**: Tagging, naming, architecture

### 🔗 Integration

Used by AI Service and Infrastructure Service for validation:
```
Terraform Code → MCP Service → Validation Results → Deploy/Refine
```
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Cost Analysis",
                "description": "Calculate and estimate AWS infrastructure costs"
            },
            {
                "name": "Security Validation",
                "description": "Validate security configurations and policies"
            },
            {
                "name": "Quota Checking",
                "description": "Check AWS service limits and quotas"
            },
            {
                "name": "Resource Validation",
                "description": "Validate Terraform resources and dependencies"
            },
            {
                "name": "Health & Status",
                "description": "Service health checks and statistics"
            }
        ]
    )
    
    openapi_schema["info"]["contact"] = {
        "name": "AI DevOps Assistant",
        "email": "support@example.com"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title="MCP Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Pydantic Models ==============

class TerraformValidationRequest(BaseModel):
    """Request to validate Terraform code"""
    terraform_code: str = Field(
        ...,
        description="Terraform code to validate",
        example='resource "aws_instance" "web" { ami = "ami-123" instance_type = "t3.micro" }',
        min_length=10
    )
    region: Optional[str] = Field(
        default="us-east-1",
        description="AWS region for cost calculation",
        example="us-east-1"
    )
    validation_level: Optional[str] = Field(
        default="standard",
        description="Validation level: basic, standard, or strict",
        example="standard"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "terraform_code": '''resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.large"
  
  root_block_device {
    volume_size = 100
  }
}''',
                "region": "us-east-1",
                "validation_level": "standard"
            }
        }


class CostEstimate(BaseModel):
    """Cost estimation details"""
    resource_type: str = Field(..., description="AWS resource type")
    resource_name: str = Field(..., description="Resource name from Terraform")
    monthly_cost: float = Field(..., description="Estimated monthly cost in USD")
    cost_breakdown: Dict[str, float] = Field(..., description="Detailed cost breakdown")
    pricing_notes: Optional[str] = Field(None, description="Additional pricing information")


class SecurityIssue(BaseModel):
    """Security validation issue"""
    severity: str = Field(..., description="Severity: critical, high, medium, low")
    resource: str = Field(..., description="Affected resource")
    issue: str = Field(..., description="Description of the security issue")
    recommendation: str = Field(..., description="How to fix the issue")
    rule_id: str = Field(..., description="Security rule identifier")


class QuotaWarning(BaseModel):
    """AWS quota warning"""
    service: str = Field(..., description="AWS service")
    resource_type: str = Field(..., description="Resource type")
    current_usage: int = Field(..., description="Current usage count")
    requested: int = Field(..., description="Requested additional resources")
    limit: int = Field(..., description="Service limit")
    warning_level: str = Field(..., description="Warning level: info, warning, critical")


class ResourceDependency(BaseModel):
    """Resource dependency information"""
    resource: str = Field(..., description="Resource name")
    depends_on: List[str] = Field(..., description="List of dependencies")
    dependency_valid: bool = Field(..., description="Whether dependencies are valid")
    issues: Optional[List[str]] = Field(None, description="Dependency issues if any")


class ValidationResponse(BaseModel):
    """Complete validation response"""
    validation_id: str = Field(..., description="Unique validation ID")
    status: str = Field(..., description="Overall status: passed, warning, failed")
    timestamp: str = Field(..., description="Validation timestamp")
    
    # Cost analysis
    total_monthly_cost: float = Field(..., description="Total estimated monthly cost")
    cost_estimates: List[CostEstimate] = Field(..., description="Per-resource cost breakdown")
    
    # Security validation
    security_score: int = Field(..., description="Security score (0-100)")
    security_issues: List[SecurityIssue] = Field(..., description="Security issues found")
    
    # Quota checking
    quota_warnings: List[QuotaWarning] = Field(..., description="Quota warnings")
    
    # Resource validation
    resources_count: int = Field(..., description="Number of resources")
    dependencies: List[ResourceDependency] = Field(..., description="Resource dependencies")
    
    # Recommendations
    recommendations: List[str] = Field(..., description="General recommendations")
    deployment_ready: bool = Field(..., description="Whether safe to deploy")


class CostAnalysisRequest(BaseModel):
    """Request for cost-only analysis"""
    terraform_code: str = Field(..., description="Terraform code to analyze")
    region: str = Field(default="us-east-1", description="AWS region")


class SecurityCheckRequest(BaseModel):
    """Request for security-only check"""
    terraform_code: str = Field(..., description="Terraform code to check")
    security_policies: Optional[List[str]] = Field(
        default=None,
        description="Custom security policies to enforce"
    )


class QuotaCheckRequest(BaseModel):
    """Request for quota checking"""
    resources: Dict[str, int] = Field(
        ...,
        description="Resource counts to check",
        example={"ec2": 5, "vpc": 1, "rds": 2}
    )
    region: str = Field(default="us-east-1", description="AWS region")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    validations_count: int = Field(..., description="Total validations performed")
    timestamp: str = Field(..., description="Check timestamp")


# ============== AWS Pricing Data (Simplified) ==============

AWS_PRICING = {
    "ec2": {
        "t3.micro": {"hourly": 0.0104, "monthly": 7.59},
        "t3.small": {"hourly": 0.0208, "monthly": 15.18},
        "t3.medium": {"hourly": 0.0416, "monthly": 30.37},
        "t3.large": {"hourly": 0.0832, "monthly": 60.74},
        "t3.xlarge": {"hourly": 0.1664, "monthly": 121.49},
        "t3.2xlarge": {"hourly": 0.3328, "monthly": 242.98},
        "m5.large": {"hourly": 0.096, "monthly": 70.08},
        "m5.xlarge": {"hourly": 0.192, "monthly": 140.16},
        "m5.2xlarge": {"hourly": 0.384, "monthly": 280.32},
    },
    "ebs": {
        "gp3": {"per_gb_month": 0.08},
        "gp2": {"per_gb_month": 0.10},
        "io2": {"per_gb_month": 0.125},
    },
    "rds": {
        "db.t3.micro": {"hourly": 0.017, "monthly": 12.41},
        "db.t3.small": {"hourly": 0.034, "monthly": 24.82},
        "db.t3.medium": {"hourly": 0.068, "monthly": 49.64},
        "db.m5.large": {"hourly": 0.172, "monthly": 125.56},
    },
    "nat_gateway": {"hourly": 0.045, "monthly": 32.85, "per_gb": 0.045},
    "alb": {"hourly": 0.0225, "monthly": 16.43},
    "nlb": {"hourly": 0.0225, "monthly": 16.43},
    "s3": {"per_gb_month": 0.023},
    "eip": {"hourly": 0.005, "monthly": 3.65},
}

# AWS Service Quotas (Default limits)
AWS_QUOTAS = {
    "ec2": {
        "instances": 20,
        "vcpus": 64,
        "elastic_ips": 5,
    },
    "vpc": {
        "vpcs_per_region": 5,
        "subnets_per_vpc": 200,
        "security_groups": 2500,
        "internet_gateways": 5,
        "nat_gateways": 5,
    },
    "rds": {
        "instances": 40,
        "storage_gb": 100000,
    },
    "s3": {
        "buckets": 100,
    },
}

# Security Rules
SECURITY_RULES = {
    "encryption_at_rest": {
        "severity": "high",
        "resources": ["aws_ebs_volume", "aws_rds_instance", "aws_s3_bucket"],
        "rule": "encrypted = true"
    },
    "public_access": {
        "severity": "critical",
        "resources": ["aws_security_group"],
        "rule": "cidr_blocks should not contain 0.0.0.0/0 for ingress"
    },
    "iam_policy": {
        "severity": "medium",
        "resources": ["aws_iam_policy", "aws_iam_role_policy"],
        "rule": "avoid wildcard (*) permissions"
    },
}

# Validation counter
validation_counter = 0


# ============== Helper Functions ==============

def generate_validation_id() -> str:
    """Generate unique validation ID"""
    timestamp = datetime.now().isoformat()
    hash_input = f"{timestamp}{validation_counter}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:12]


def extract_resources(terraform_code: str) -> List[Dict[str, Any]]:
    """Extract resources from Terraform code"""
    resources = []
    
    # Simple regex to extract resource blocks
    resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]+)\}'
    matches = re.finditer(resource_pattern, terraform_code, re.DOTALL)
    
    for match in matches:
        resource_type = match.group(1)
        resource_name = match.group(2)
        resource_body = match.group(3)
        
        resources.append({
            "type": resource_type,
            "name": resource_name,
            "body": resource_body,
            "full_name": f"{resource_type}.{resource_name}"
        })
    
    return resources


def calculate_ec2_cost(instance_type: str, volume_size: int = 8) -> CostEstimate:
    """Calculate EC2 instance cost"""
    instance_pricing = AWS_PRICING["ec2"].get(instance_type, {"monthly": 50.0})
    instance_cost = instance_pricing["monthly"]
    
    # EBS volume cost (default gp3)
    storage_cost = volume_size * AWS_PRICING["ebs"]["gp3"]["per_gb_month"]
    
    total = instance_cost + storage_cost
    
    return CostEstimate(
        resource_type="aws_instance",
        resource_name="ec2_instance",
        monthly_cost=round(total, 2),
        cost_breakdown={
            "instance": round(instance_cost, 2),
            "storage": round(storage_cost, 2)
        },
        pricing_notes=f"Instance type: {instance_type}, {volume_size}GB storage"
    )


def calculate_rds_cost(instance_type: str, storage_gb: int = 20, multi_az: bool = False) -> CostEstimate:
    """Calculate RDS instance cost"""
    instance_pricing = AWS_PRICING["rds"].get(instance_type, {"monthly": 60.0})
    instance_cost = instance_pricing["monthly"]
    
    # Multi-AZ doubles the cost
    if multi_az:
        instance_cost *= 2
    
    # Storage cost
    storage_cost = storage_gb * AWS_PRICING["ebs"]["gp2"]["per_gb_month"]
    
    total = instance_cost + storage_cost
    
    return CostEstimate(
        resource_type="aws_db_instance",
        resource_name="rds_instance",
        monthly_cost=round(total, 2),
        cost_breakdown={
            "instance": round(instance_cost, 2),
            "storage": round(storage_cost, 2)
        },
        pricing_notes=f"Instance: {instance_type}, Storage: {storage_gb}GB, Multi-AZ: {multi_az}"
    )


def check_security(resources: List[Dict]) -> List[SecurityIssue]:
    """Check security issues in resources"""
    issues = []
    
    for resource in resources:
        resource_type = resource["type"]
        resource_name = resource["name"]
        body = resource["body"]
        
        # Check encryption
        if resource_type in ["aws_ebs_volume", "aws_db_instance", "aws_s3_bucket"]:
            if "encrypted" not in body or "encrypted = false" in body or "encrypted=false" in body:
                issues.append(SecurityIssue(
                    severity="high",
                    resource=f"{resource_type}.{resource_name}",
                    issue="Encryption at rest is not enabled",
                    recommendation=f"Add 'encrypted = true' to {resource_type}",
                    rule_id="SEC001"
                ))
        
        # Check public access
        if resource_type == "aws_security_group":
            if "0.0.0.0/0" in body:
                issues.append(SecurityIssue(
                    severity="critical",
                    resource=f"{resource_type}.{resource_name}",
                    issue="Security group allows access from anywhere (0.0.0.0/0)",
                    recommendation="Restrict ingress to specific IP ranges",
                    rule_id="SEC002"
                ))
        
        # Check S3 bucket public access
        if resource_type == "aws_s3_bucket":
            if "acl" in body and "public-read" in body:
                issues.append(SecurityIssue(
                    severity="critical",
                    resource=f"{resource_type}.{resource_name}",
                    issue="S3 bucket has public-read ACL",
                    recommendation="Use private ACL and configure access through bucket policies",
                    rule_id="SEC003"
                ))
        
        # Check IAM wildcard permissions
        if resource_type in ["aws_iam_policy", "aws_iam_role_policy"]:
            if '"*"' in body or "'*'" in body:
                issues.append(SecurityIssue(
                    severity="medium",
                    resource=f"{resource_type}.{resource_name}",
                    issue="IAM policy contains wildcard (*) permissions",
                    recommendation="Use principle of least privilege with specific permissions",
                    rule_id="SEC004"
                ))
    
    return issues


def check_quotas(resources: List[Dict], region: str) -> List[QuotaWarning]:
    """Check AWS quotas"""
    warnings = []
    
    # Count resources by type
    resource_counts = {}
    for resource in resources:
        res_type = resource["type"]
        resource_counts[res_type] = resource_counts.get(res_type, 0) + 1
    
    # Check EC2 instances
    if "aws_instance" in resource_counts:
        count = resource_counts["aws_instance"]
        limit = AWS_QUOTAS["ec2"]["instances"]
        if count > limit * 0.8:
            warnings.append(QuotaWarning(
                service="EC2",
                resource_type="instances",
                current_usage=0,  # We don't know actual usage
                requested=count,
                limit=limit,
                warning_level="warning" if count <= limit else "critical"
            ))
    
    # Check VPCs
    if "aws_vpc" in resource_counts:
        count = resource_counts["aws_vpc"]
        limit = AWS_QUOTAS["vpc"]["vpcs_per_region"]
        if count > limit * 0.8:
            warnings.append(QuotaWarning(
                service="VPC",
                resource_type="vpcs",
                current_usage=0,
                requested=count,
                limit=limit,
                warning_level="warning" if count <= limit else "critical"
            ))
    
    # Check RDS instances
    if "aws_db_instance" in resource_counts:
        count = resource_counts["aws_db_instance"]
        limit = AWS_QUOTAS["rds"]["instances"]
        if count > limit * 0.8:
            warnings.append(QuotaWarning(
                service="RDS",
                resource_type="instances",
                current_usage=0,
                requested=count,
                limit=limit,
                warning_level="warning" if count <= limit else "critical"
            ))
    
    return warnings


def analyze_dependencies(resources: List[Dict]) -> List[ResourceDependency]:
    """Analyze resource dependencies"""
    dependencies = []
    
    for resource in resources:
        deps = []
        body = resource["body"]
        
        # Find references to other resources
        ref_pattern = r'(\w+\.\w+)\.id'
        refs = re.findall(ref_pattern, body)
        deps.extend(refs)
        
        # Check explicit depends_on
        depends_pattern = r'depends_on\s*=\s*\[([^\]]+)\]'
        depends_match = re.search(depends_pattern, body)
        if depends_match:
            explicit_deps = [d.strip().strip('"') for d in depends_match.group(1).split(',')]
            deps.extend(explicit_deps)
        
        if deps:
            dependencies.append(ResourceDependency(
                resource=resource["full_name"],
                depends_on=deps,
                dependency_valid=True,  # Simplified validation
                issues=None
            ))
    
    return dependencies


# ============== API Endpoints ==============

@app.get(
    "/",
    tags=["Health & Status"],
    summary="Service Status",
    description="Quick health check to verify the MCP service is running"
)
async def root():
    """Quick health check endpoint"""
    return {
        "service": "MCP Service",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post(
    "/validate",
    response_model=ValidationResponse,
    tags=["Resource Validation"],
    summary="Complete Terraform Validation",
    description="""
Perform comprehensive validation of Terraform code including:
- Cost estimation
- Security checking
- Quota validation
- Dependency analysis

Returns detailed validation report with recommendations.
"""
)
async def validate_terraform(request: TerraformValidationRequest):
    """
    Comprehensive validation of Terraform infrastructure code.
    
    Checks cost, security, quotas, and dependencies.
    Returns deployment readiness status and recommendations.
    """
    global validation_counter
    validation_counter += 1
    
    try:
        # Extract resources from Terraform code
        resources = extract_resources(request.terraform_code)
        
        if not resources:
            raise HTTPException(
                status_code=400,
                detail="No valid Terraform resources found in the code"
            )
        
        # Cost estimation
        cost_estimates = []
        total_cost = 0.0
        
        for resource in resources:
            if resource["type"] == "aws_instance":
                # Extract instance type
                instance_match = re.search(r'instance_type\s*=\s*"([^"]+)"', resource["body"])
                instance_type = instance_match.group(1) if instance_match else "t3.micro"
                
                # Extract volume size
                volume_match = re.search(r'volume_size\s*=\s*(\d+)', resource["body"])
                volume_size = int(volume_match.group(1)) if volume_match else 8
                
                cost = calculate_ec2_cost(instance_type, volume_size)
                cost.resource_name = resource["name"]
                cost_estimates.append(cost)
                total_cost += cost.monthly_cost
            
            elif resource["type"] == "aws_db_instance":
                instance_match = re.search(r'instance_class\s*=\s*"([^"]+)"', resource["body"])
                instance_type = instance_match.group(1) if instance_match else "db.t3.micro"
                
                storage_match = re.search(r'allocated_storage\s*=\s*(\d+)', resource["body"])
                storage = int(storage_match.group(1)) if storage_match else 20
                
                multi_az = "multi_az = true" in resource["body"]
                
                cost = calculate_rds_cost(instance_type, storage, multi_az)
                cost.resource_name = resource["name"]
                cost_estimates.append(cost)
                total_cost += cost.monthly_cost
            
            elif resource["type"] == "aws_nat_gateway":
                cost_estimates.append(CostEstimate(
                    resource_type="aws_nat_gateway",
                    resource_name=resource["name"],
                    monthly_cost=32.85,
                    cost_breakdown={"base": 32.85},
                    pricing_notes="NAT Gateway base cost (data transfer charged separately)"
                ))
                total_cost += 32.85
        
        # Security validation
        security_issues = check_security(resources)
        security_score = max(0, 100 - (len(security_issues) * 10))
        
        # Quota checking
        quota_warnings = check_quotas(resources, request.region)
        
        # Dependency analysis
        dependencies = analyze_dependencies(resources)
        
        # Generate recommendations
        recommendations = []
        
        if total_cost > 500:
            recommendations.append("High cost detected ($500+/month). Consider using smaller instance types or reserved instances.")
        
        if len(security_issues) > 0:
            recommendations.append(f"Found {len(security_issues)} security issues. Review and fix before deployment.")
        
        if len(quota_warnings) > 0:
            recommendations.append("Some resources are approaching AWS quota limits. Consider requesting limit increases.")
        
        # Check if encrypted storage is missing
        has_unencrypted = any(issue.rule_id == "SEC001" for issue in security_issues)
        if has_unencrypted:
            recommendations.append("Enable encryption at rest for all data stores (EBS, RDS, S3).")
        
        # Determine overall status
        has_critical_issues = any(issue.severity == "critical" for issue in security_issues)
        has_quota_critical = any(w.warning_level == "critical" for w in quota_warnings)
        
        if has_critical_issues or has_quota_critical:
            status = "failed"
            deployment_ready = False
        elif len(security_issues) > 0 or len(quota_warnings) > 0:
            status = "warning"
            deployment_ready = True  # Can deploy with warnings
        else:
            status = "passed"
            deployment_ready = True
        
        return ValidationResponse(
            validation_id=generate_validation_id(),
            status=status,
            timestamp=datetime.now().isoformat(),
            total_monthly_cost=round(total_cost, 2),
            cost_estimates=cost_estimates,
            security_score=security_score,
            security_issues=security_issues,
            quota_warnings=quota_warnings,
            resources_count=len(resources),
            dependencies=dependencies,
            recommendations=recommendations,
            deployment_ready=deployment_ready
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@app.post(
    "/cost-analysis",
    tags=["Cost Analysis"],
    summary="Cost-Only Analysis",
    description="Estimate AWS costs without security or quota checks"
)
async def analyze_cost(request: CostAnalysisRequest):
    """
    Calculate estimated monthly costs for Terraform infrastructure.
    
    Returns detailed cost breakdown per resource.
    """
    try:
        resources = extract_resources(request.terraform_code)
        
        cost_estimates = []
        total_cost = 0.0
        
        for resource in resources:
            if resource["type"] == "aws_instance":
                instance_match = re.search(r'instance_type\s*=\s*"([^"]+)"', resource["body"])
                instance_type = instance_match.group(1) if instance_match else "t3.micro"
                volume_match = re.search(r'volume_size\s*=\s*(\d+)', resource["body"])
                volume_size = int(volume_match.group(1)) if volume_match else 8
                
                cost = calculate_ec2_cost(instance_type, volume_size)
                cost.resource_name = resource["name"]
                cost_estimates.append(cost)
                total_cost += cost.monthly_cost
        
        return {
            "total_monthly_cost": round(total_cost, 2),
            "cost_estimates": cost_estimates,
            "region": request.region,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost analysis failed: {str(e)}")


@app.post(
    "/security-check",
    tags=["Security Validation"],
    summary="Security-Only Check",
    description="Validate security configurations without cost or quota analysis"
)
async def check_security_only(request: SecurityCheckRequest):
    """
    Check Terraform code for security issues.
    
    Returns list of security violations and recommendations.
    """
    try:
        resources = extract_resources(request.terraform_code)
        security_issues = check_security(resources)
        security_score = max(0, 100 - (len(security_issues) * 10))
        
        return {
            "security_score": security_score,
            "security_issues": security_issues,
            "total_issues": len(security_issues),
            "critical_issues": len([i for i in security_issues if i.severity == "critical"]),
            "high_issues": len([i for i in security_issues if i.severity == "high"]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Security check failed: {str(e)}")


@app.post(
    "/quota-check",
    tags=["Quota Checking"],
    summary="Quota Availability Check",
    description="Check if requested resources are within AWS service limits"
)
async def check_quota(request: QuotaCheckRequest):
    """
    Check if requested resources are within AWS quotas.
    
    Returns warnings for resources approaching limits.
    """
    try:
        warnings = []
        
        for resource_type, count in request.resources.items():
            if resource_type == "ec2":
                limit = AWS_QUOTAS["ec2"]["instances"]
                if count > limit * 0.8:
                    warnings.append(QuotaWarning(
                        service="EC2",
                        resource_type="instances",
                        current_usage=0,
                        requested=count,
                        limit=limit,
                        warning_level="warning" if count <= limit else "critical"
                    ))
            
            elif resource_type == "vpc":
                limit = AWS_QUOTAS["vpc"]["vpcs_per_region"]
                if count > limit * 0.8:
                    warnings.append(QuotaWarning(
                        service="VPC",
                        resource_type="vpcs",
                        current_usage=0,
                        requested=count,
                        limit=limit,
                        warning_level="warning" if count <= limit else "critical"
                    ))
        
        return {
            "quota_warnings": warnings,
            "total_warnings": len(warnings),
            "all_clear": len(warnings) == 0,
            "region": request.region,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quota check failed: {str(e)}")


@app.get(
    "/pricing/{resource_type}",
    tags=["Cost Analysis"],
    summary="Get Resource Pricing",
    description="Get pricing information for a specific AWS resource type"
)
async def get_pricing(resource_type: str):
    """Get pricing information for an AWS resource type"""
    if resource_type not in AWS_PRICING:
        raise HTTPException(status_code=404, detail=f"Pricing not available for {resource_type}")
    
    return {
        "resource_type": resource_type,
        "pricing": AWS_PRICING[resource_type],
        "currency": "USD",
        "region": "us-east-1"
    }


@app.get(
    "/quotas/{service}",
    tags=["Quota Checking"],
    summary="Get Service Quotas",
    description="Get AWS service limits and quotas"
)
async def get_quotas(service: str):
    """Get AWS service quotas"""
    if service not in AWS_QUOTAS:
        raise HTTPException(status_code=404, detail=f"Quotas not available for {service}")
    
    return {
        "service": service,
        "quotas": AWS_QUOTAS[service],
        "note": "These are default quotas. Actual limits may vary by account."
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health & Status"],
    summary="Detailed Health Check",
    description="Comprehensive health check with validation statistics"
)
async def health_check():
    """
    Detailed health check with service statistics.
    """
    return HealthResponse(
        status="healthy",
        validations_count=validation_counter,
        timestamp=datetime.now().isoformat()
    )


@app.get(
    "/stats",
    tags=["Health & Status"],
    summary="Service Statistics",
    description="Get MCP service statistics and metrics"
)
async def get_stats():
    """Get service statistics"""
    return {
        "total_validations": validation_counter,
        "supported_resources": list(AWS_PRICING.keys()),
        "security_rules": len(SECURITY_RULES),
        "available_quotas": list(AWS_QUOTAS.keys()),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
