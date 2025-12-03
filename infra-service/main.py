"""
Infrastructure Service - Terraform Deployment & Management
Handles Terraform initialization, planning, applying, and state management
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import subprocess
import os
import json
import hashlib
import shutil
import logging
from datetime import datetime
from pathlib import Path
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom OpenAPI schema for Swagger documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="🚀 Infrastructure Service - Terraform Deployment",
        version="1.0.0",
        description="""
## Terraform Deployment & State Management Service

This service manages the complete Terraform deployment lifecycle:
- **Initialization**: Set up Terraform working directory
- **Planning**: Generate execution plans
- **Deployment**: Apply infrastructure changes
- **Destruction**: Clean up resources
- **State Management**: Track deployment state

### 🎯 Key Features

- Automated Terraform workflow execution
- Real-time deployment status tracking
- State management and versioning
- Rollback capabilities
- Deployment history and logs
- AWS credential management

### 🔄 Typical Workflow

1. Receive validated Terraform code from AI/MCP services
2. Initialize Terraform working directory
3. Generate execution plan
4. Apply infrastructure changes to AWS
5. Track state and report status
6. Store deployment metadata

### 📊 Deployment States

- **pending**: Deployment queued
- **initializing**: Terraform init running
- **planning**: Generating execution plan
- **applying**: Creating infrastructure
- **completed**: Successfully deployed
- **failed**: Deployment failed
- **destroying**: Tearing down resources

### 🔗 Integration

Final step in the deployment pipeline:
```
AI → MCP Validation → Infrastructure Service → AWS
```
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Deployments",
                "description": "Create and manage infrastructure deployments"
            },
            {
                "name": "Terraform Operations",
                "description": "Execute Terraform commands (init, plan, apply, destroy)"
            },
            {
                "name": "State Management",
                "description": "Manage Terraform state and deployment history"
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
    title="Infrastructure Service",
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

# Configuration
WORKSPACE_DIR = Path("/app/workspaces")
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# In-memory deployment tracking (use database in production)
deployments_db = {}
deployment_counter = 0


# ============== Pydantic Models ==============

class DeploymentRequest(BaseModel):
    """Request to deploy infrastructure"""
    terraform_code: str = Field(
        ...,
        description="Terraform code to deploy",
        min_length=10
    )
    deployment_name: str = Field(
        ...,
        description="Name for this deployment",
        example="production-vpc"
    )
    region: Optional[str] = Field(
        default="us-east-1",
        description="AWS region",
        example="us-east-1"
    )
    auto_approve: Optional[bool] = Field(
        default=False,
        description="Auto-approve deployment without manual confirmation"
    )
    tags: Optional[Dict[str, str]] = Field(
        default=None,
        description="Tags for deployment tracking"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "terraform_code": '''resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "production-vpc"
  }
}''',
                "deployment_name": "production-vpc",
                "region": "us-east-1",
                "auto_approve": False,
                "tags": {
                    "Environment": "production",
                    "Team": "platform"
                }
            }
        }


class DeploymentResponse(BaseModel):
    """Response after creating deployment"""
    deployment_id: str = Field(..., description="Unique deployment ID")
    status: str = Field(..., description="Current deployment status")
    message: str = Field(..., description="Status message")
    workspace_path: str = Field(..., description="Workspace directory path")
    created_at: str = Field(..., description="Creation timestamp")


class DeploymentStatus(BaseModel):
    """Deployment status information"""
    deployment_id: str
    deployment_name: str
    status: str
    current_step: str
    progress_percentage: int
    created_at: str
    updated_at: str
    terraform_output: Optional[str] = None
    error_message: Optional[str] = None
    resources_created: Optional[List[str]] = None


class TerraformPlanRequest(BaseModel):
    """Request to generate Terraform plan"""
    deployment_id: str = Field(..., description="Deployment ID")


class TerraformPlanResponse(BaseModel):
    """Terraform plan response"""
    deployment_id: str
    plan_output: str
    resources_to_add: int
    resources_to_change: int
    resources_to_destroy: int
    plan_file_path: str


class DeploymentListResponse(BaseModel):
    """List of deployments"""
    total: int
    deployments: List[DeploymentStatus]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    terraform_version: str
    active_deployments: int
    total_deployments: int
    timestamp: str


# ============== Helper Functions ==============

def generate_deployment_id() -> str:
    """Generate unique deployment ID"""
    global deployment_counter
    deployment_counter += 1
    timestamp = datetime.now().isoformat()
    hash_input = f"{timestamp}{deployment_counter}{uuid.uuid4()}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:16]


def get_workspace_path(deployment_id: str) -> Path:
    """Get workspace directory path for deployment"""
    return WORKSPACE_DIR / deployment_id


def run_terraform_command(workspace_path: Path, command: List[str], env: Dict = None) -> tuple:
    """
    Run a Terraform command in the workspace
    
    Returns: (success: bool, output: str, error: str)
    """
    try:
        # Merge environment variables
        terraform_env = os.environ.copy()
        if env:
            terraform_env.update(env)
        
        # Log the command for debugging
        logger.info(f"Running command in {workspace_path}: {' '.join(command)}")
        logger.info(f"Environment variables: AWS_REGION={terraform_env.get('AWS_REGION', 'not set')}")
        
        # Check if workspace exists
        if not workspace_path.exists():
            error_msg = f"Workspace path does not exist: {workspace_path}"
            logger.error(error_msg)
            return False, "", error_msg
        
        # Check if Terraform files exist
        main_tf = workspace_path / "main.tf"
        if not main_tf.exists():
            error_msg = f"main.tf not found in {workspace_path}"
            logger.error(error_msg)
            return False, "", error_msg
        
        # Run command
        result = subprocess.run(
            command,
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            env=terraform_env
        )
        
        # Log output
        logger.info(f"Command exit code: {result.returncode}")
        if result.stdout:
            logger.info(f"Command stdout: {result.stdout[:500]}")
        if result.stderr:
            logger.warning(f"Command stderr: {result.stderr[:500]}")
        
        success = result.returncode == 0
        return success, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        error_msg = "Command timed out after 10 minutes"
        logger.error(error_msg)
        return False, "", error_msg
    except Exception as e:
        error_msg = f"Exception running Terraform: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, "", error_msg


def create_terraform_files(workspace_path: Path, terraform_code: str, region: str):
    """Create Terraform configuration files in workspace"""
    # Create main.tf
    main_tf = workspace_path / "main.tf"
    main_tf.write_text(terraform_code)
    
    logger.info(f"Created main.tf in {workspace_path}")
    
    # Check if terraform_code already contains provider configuration
    has_terraform_block = 'terraform {' in terraform_code or 'terraform{' in terraform_code
    has_provider_block = 'provider "aws"' in terraform_code or "provider 'aws'" in terraform_code
    has_required_providers = 'required_providers' in terraform_code
    
    logger.info(f"Code analysis: terraform_block={has_terraform_block}, provider_block={has_provider_block}, required_providers={has_required_providers}")
    
    # Only create provider.tf if the code doesn't already have provider configuration
    if not (has_terraform_block and has_required_providers):
        logger.info("Creating provider.tf (code doesn't have complete provider configuration)")
        provider_tf = workspace_path / "provider.tf"
        provider_content = f'''terraform {{
  required_version = ">= 1.0"
  
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{region}"
}}
'''
        provider_tf.write_text(provider_content)
    else:
        logger.info("Skipping provider.tf creation (code already has provider configuration)")
        # If code has terraform block but no provider block, just add the provider
        if has_terraform_block and not has_provider_block:
            logger.info("Adding minimal provider.tf (only provider block)")
            provider_tf = workspace_path / "provider.tf"
            provider_content = f'''provider "aws" {{
  region = "{region}"
}}
'''
            provider_tf.write_text(provider_content)
    
    # Create terraform.tfvars (if needed)
    tfvars = workspace_path / "terraform.tfvars"
    tfvars.write_text(f'# Deployment variables\nregion = "{region}"\n')
    
    logger.info("Terraform files created successfully")


def parse_terraform_plan(plan_output: str) -> Dict[str, int]:
    """Parse Terraform plan output to count resources"""
    import re
    
    counts = {
        "add": 0,
        "change": 0,
        "destroy": 0
    }
    
    # Look for plan summary
    summary_pattern = r"Plan: (\d+) to add, (\d+) to change, (\d+) to destroy"
    match = re.search(summary_pattern, plan_output)
    
    if match:
        counts["add"] = int(match.group(1))
        counts["change"] = int(match.group(2))
        counts["destroy"] = int(match.group(3))
    
    return counts


def extract_created_resources(apply_output: str) -> List[str]:
    """Extract list of created resources from terraform apply output"""
    import re
    
    resources = []
    
    # Look for resource creation messages
    pattern = r"(aws_[\w]+\.[\w]+): Creation complete"
    matches = re.findall(pattern, apply_output)
    
    resources.extend(matches)
    
    return resources


# ============== API Endpoints ==============

@app.get(
    "/",
    tags=["Health & Status"],
    summary="Service Status",
    description="Quick health check to verify the Infrastructure service is running"
)
async def root():
    """Quick health check endpoint"""
    return {
        "service": "Infrastructure Service",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post(
    "/deployments",
    response_model=DeploymentResponse,
    tags=["Deployments"],
    summary="Create New Deployment",
    description="""
Create a new infrastructure deployment.

This endpoint:
1. Creates a workspace directory
2. Writes Terraform files
3. Queues deployment for execution

Use `/deployments/{id}/apply` to execute the deployment.
"""
)
async def create_deployment(request: DeploymentRequest):
    """
    Create a new infrastructure deployment.
    
    Sets up workspace and prepares for Terraform execution.
    """
    try:
        # Generate deployment ID
        deployment_id = generate_deployment_id()
        
        # Create workspace
        workspace_path = get_workspace_path(deployment_id)
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Create Terraform files
        create_terraform_files(workspace_path, request.terraform_code, request.region)
        
        # Store deployment info
        deployment_info = {
            "deployment_id": deployment_id,
            "deployment_name": request.deployment_name,
            "status": "pending",
            "current_step": "created",
            "progress_percentage": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "region": request.region,
            "auto_approve": request.auto_approve,
            "tags": request.tags or {},
            "terraform_code": request.terraform_code,
            "workspace_path": str(workspace_path),
            "terraform_output": "",
            "error_message": None,
            "resources_created": []
        }
        
        deployments_db[deployment_id] = deployment_info
        
        return DeploymentResponse(
            deployment_id=deployment_id,
            status="pending",
            message="Deployment created successfully. Use /deployments/{id}/init to initialize.",
            workspace_path=str(workspace_path),
            created_at=deployment_info["created_at"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create deployment: {str(e)}")


@app.post(
    "/deployments/{deployment_id}/init",
    tags=["Terraform Operations"],
    summary="Initialize Terraform",
    description="Run 'terraform init' to initialize the workspace"
)
async def terraform_init(deployment_id: str, background_tasks: BackgroundTasks):
    """
    Initialize Terraform workspace.
    
    Runs `terraform init` to download providers and set up backend.
    """
    if deployment_id not in deployments_db:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    deployment = deployments_db[deployment_id]
    workspace_path = Path(deployment["workspace_path"])
    
    # Update status
    deployment["status"] = "initializing"
    deployment["current_step"] = "terraform init"
    deployment["progress_percentage"] = 10
    deployment["updated_at"] = datetime.now().isoformat()
    
    try:
        # Run terraform init
        success, stdout, stderr = run_terraform_command(
            workspace_path,
            ["terraform", "init", "-no-color"]
        )
        
        deployment["terraform_output"] += f"\n=== TERRAFORM INIT ===\n{stdout}\n{stderr}\n"
        
        if success:
            deployment["status"] = "initialized"
            deployment["current_step"] = "init complete"
            deployment["progress_percentage"] = 25
            deployment["updated_at"] = datetime.now().isoformat()
            
            return {
                "deployment_id": deployment_id,
                "status": "initialized",
                "message": "Terraform initialized successfully",
                "output": stdout
            }
        else:
            deployment["status"] = "failed"
            deployment["error_message"] = f"Init failed: {stderr}"
            deployment["updated_at"] = datetime.now().isoformat()
            
            raise HTTPException(status_code=500, detail=f"Terraform init failed: {stderr}")
            
    except Exception as e:
        deployment["status"] = "failed"
        deployment["error_message"] = str(e)
        deployment["updated_at"] = datetime.now().isoformat()
        raise HTTPException(status_code=500, detail=f"Init failed: {str(e)}")


@app.post(
    "/deployments/{deployment_id}/plan",
    response_model=TerraformPlanResponse,
    tags=["Terraform Operations"],
    summary="Generate Terraform Plan",
    description="Run 'terraform plan' to preview infrastructure changes"
)
async def terraform_plan(deployment_id: str):
    """
    Generate Terraform execution plan.
    
    Shows what resources will be created, modified, or destroyed.
    """
    if deployment_id not in deployments_db:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    deployment = deployments_db[deployment_id]
    workspace_path = Path(deployment["workspace_path"])
    
    if deployment["status"] != "initialized":
        raise HTTPException(
            status_code=400,
            detail="Deployment must be initialized before planning. Run /init first."
        )
    
    # Update status
    deployment["status"] = "planning"
    deployment["current_step"] = "terraform plan"
    deployment["progress_percentage"] = 40
    deployment["updated_at"] = datetime.now().isoformat()
    
    try:
        # Run terraform plan
        plan_file = workspace_path / "tfplan"
        success, stdout, stderr = run_terraform_command(
            workspace_path,
            ["terraform", "plan", "-out=tfplan", "-no-color"]
        )
        
        deployment["terraform_output"] += f"\n=== TERRAFORM PLAN ===\n{stdout}\n{stderr}\n"
        
        if success:
            # Parse plan output
            counts = parse_terraform_plan(stdout)
            
            deployment["status"] = "planned"
            deployment["current_step"] = "plan complete"
            deployment["progress_percentage"] = 50
            deployment["updated_at"] = datetime.now().isoformat()
            
            return TerraformPlanResponse(
                deployment_id=deployment_id,
                plan_output=stdout,
                resources_to_add=counts["add"],
                resources_to_change=counts["change"],
                resources_to_destroy=counts["destroy"],
                plan_file_path=str(plan_file)
            )
        else:
            deployment["status"] = "failed"
            deployment["error_message"] = f"Plan failed: {stderr}"
            deployment["updated_at"] = datetime.now().isoformat()
            
            raise HTTPException(status_code=500, detail=f"Terraform plan failed: {stderr}")
            
    except Exception as e:
        deployment["status"] = "failed"
        deployment["error_message"] = str(e)
        deployment["updated_at"] = datetime.now().isoformat()
        raise HTTPException(status_code=500, detail=f"Plan failed: {str(e)}")


@app.post(
    "/deployments/{deployment_id}/apply",
    tags=["Terraform Operations"],
    summary="Apply Terraform Changes",
    description="Run 'terraform apply' to create/update infrastructure"
)
async def terraform_apply(deployment_id: str, auto_approve: bool = False):
    """
    Apply Terraform plan to create infrastructure.
    
    This actually creates the AWS resources.
    """
    if deployment_id not in deployments_db:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    deployment = deployments_db[deployment_id]
    workspace_path = Path(deployment["workspace_path"])
    
    if deployment["status"] not in ["planned", "initialized"]:
        raise HTTPException(
            status_code=400,
            detail="Deployment must be planned before applying. Run /plan first."
        )
    
    # Check auto-approve
    if not auto_approve and not deployment.get("auto_approve"):
        raise HTTPException(
            status_code=400,
            detail="Manual approval required. Set auto_approve=true to proceed."
        )
    
    # Update status
    deployment["status"] = "applying"
    deployment["current_step"] = "terraform apply"
    deployment["progress_percentage"] = 60
    deployment["updated_at"] = datetime.now().isoformat()
    
    try:
        # Run terraform apply
        command = ["terraform", "apply", "-no-color"]
        
        # Use plan file if it exists
        plan_file = workspace_path / "tfplan"
        if plan_file.exists():
            command.extend(["-auto-approve", "tfplan"])
        else:
            command.append("-auto-approve")
        
        success, stdout, stderr = run_terraform_command(workspace_path, command)
        
        deployment["terraform_output"] += f"\n=== TERRAFORM APPLY ===\n{stdout}\n{stderr}\n"
        
        if success:
            # Extract created resources
            resources = extract_created_resources(stdout)
            
            deployment["status"] = "completed"
            deployment["current_step"] = "deployment complete"
            deployment["progress_percentage"] = 100
            deployment["resources_created"] = resources
            deployment["updated_at"] = datetime.now().isoformat()
            
            return {
                "deployment_id": deployment_id,
                "status": "completed",
                "message": "Infrastructure deployed successfully",
                "resources_created": resources,
                "output": stdout
            }
        else:
            deployment["status"] = "failed"
            deployment["error_message"] = f"Apply failed: {stderr}"
            deployment["updated_at"] = datetime.now().isoformat()
            
            raise HTTPException(status_code=500, detail=f"Terraform apply failed: {stderr}")
            
    except Exception as e:
        deployment["status"] = "failed"
        deployment["error_message"] = str(e)
        deployment["updated_at"] = datetime.now().isoformat()
        raise HTTPException(status_code=500, detail=f"Apply failed: {str(e)}")


@app.post(
    "/deployments/{deployment_id}/destroy",
    tags=["Terraform Operations"],
    summary="Destroy Infrastructure",
    description="Run 'terraform destroy' to delete all resources"
)
async def terraform_destroy(deployment_id: str, auto_approve: bool = False):
    """
    Destroy infrastructure created by this deployment.
    
    Deletes all AWS resources. Use with caution!
    """
    if deployment_id not in deployments_db:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    deployment = deployments_db[deployment_id]
    workspace_path = Path(deployment["workspace_path"])
    
    if not auto_approve:
        raise HTTPException(
            status_code=400,
            detail="Auto-approve required for destroy operations. Set auto_approve=true."
        )
    
    # Update status
    deployment["status"] = "destroying"
    deployment["current_step"] = "terraform destroy"
    deployment["progress_percentage"] = 70
    deployment["updated_at"] = datetime.now().isoformat()
    
    try:
        # Run terraform destroy
        success, stdout, stderr = run_terraform_command(
            workspace_path,
            ["terraform", "destroy", "-auto-approve", "-no-color"]
        )
        
        deployment["terraform_output"] += f"\n=== TERRAFORM DESTROY ===\n{stdout}\n{stderr}\n"
        
        if success:
            deployment["status"] = "destroyed"
            deployment["current_step"] = "destruction complete"
            deployment["progress_percentage"] = 100
            deployment["updated_at"] = datetime.now().isoformat()
            
            return {
                "deployment_id": deployment_id,
                "status": "destroyed",
                "message": "Infrastructure destroyed successfully",
                "output": stdout
            }
        else:
            deployment["status"] = "failed"
            deployment["error_message"] = f"Destroy failed: {stderr}"
            deployment["updated_at"] = datetime.now().isoformat()
            
            raise HTTPException(status_code=500, detail=f"Terraform destroy failed: {stderr}")
            
    except Exception as e:
        deployment["status"] = "failed"
        deployment["error_message"] = str(e)
        deployment["updated_at"] = datetime.now().isoformat()
        raise HTTPException(status_code=500, detail=f"Destroy failed: {str(e)}")


@app.get(
    "/deployments/{deployment_id}",
    response_model=DeploymentStatus,
    tags=["Deployments"],
    summary="Get Deployment Status",
    description="Get current status and details of a deployment"
)
async def get_deployment_status(deployment_id: str):
    """Get status of a specific deployment"""
    if deployment_id not in deployments_db:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    deployment = deployments_db[deployment_id]
    
    return DeploymentStatus(
        deployment_id=deployment["deployment_id"],
        deployment_name=deployment["deployment_name"],
        status=deployment["status"],
        current_step=deployment["current_step"],
        progress_percentage=deployment["progress_percentage"],
        created_at=deployment["created_at"],
        updated_at=deployment["updated_at"],
        terraform_output=deployment.get("terraform_output"),
        error_message=deployment.get("error_message"),
        resources_created=deployment.get("resources_created")
    )


@app.get(
    "/deployments",
    response_model=DeploymentListResponse,
    tags=["Deployments"],
    summary="List All Deployments",
    description="Get list of all deployments with their status"
)
async def list_deployments(status: Optional[str] = None, limit: int = 50):
    """List all deployments, optionally filtered by status"""
    deployments = []
    
    for deployment in deployments_db.values():
        if status and deployment["status"] != status:
            continue
        
        deployments.append(DeploymentStatus(
            deployment_id=deployment["deployment_id"],
            deployment_name=deployment["deployment_name"],
            status=deployment["status"],
            current_step=deployment["current_step"],
            progress_percentage=deployment["progress_percentage"],
            created_at=deployment["created_at"],
            updated_at=deployment["updated_at"],
            resources_created=deployment.get("resources_created")
        ))
    
    # Sort by created_at (newest first)
    deployments.sort(key=lambda x: x.created_at, reverse=True)
    
    return DeploymentListResponse(
        total=len(deployments),
        deployments=deployments[:limit]
    )


@app.delete(
    "/deployments/{deployment_id}",
    tags=["Deployments"],
    summary="Delete Deployment Record",
    description="Delete deployment record and workspace (does not destroy infrastructure)"
)
async def delete_deployment(deployment_id: str, delete_workspace: bool = False):
    """
    Delete deployment record.
    
    Note: This does not destroy AWS resources. Use /destroy first.
    """
    if deployment_id not in deployments_db:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    deployment = deployments_db[deployment_id]
    
    # Optionally delete workspace
    if delete_workspace:
        workspace_path = Path(deployment["workspace_path"])
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
    
    # Remove from database
    del deployments_db[deployment_id]
    
    return {
        "status": "success",
        "message": f"Deployment {deployment_id} deleted",
        "workspace_deleted": delete_workspace
    }


@app.get(
    "/deployments/{deployment_id}/output",
    tags=["Terraform Operations"],
    summary="Get Terraform Output",
    description="Get output values from deployed infrastructure"
)
async def get_terraform_output(deployment_id: str):
    """Get Terraform output values"""
    if deployment_id not in deployments_db:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    deployment = deployments_db[deployment_id]
    workspace_path = Path(deployment["workspace_path"])
    
    if deployment["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Deployment must be completed to get outputs"
        )
    
    try:
        # Run terraform output
        success, stdout, stderr = run_terraform_command(
            workspace_path,
            ["terraform", "output", "-json"]
        )
        
        if success:
            outputs = json.loads(stdout) if stdout else {}
            return {
                "deployment_id": deployment_id,
                "outputs": outputs
            }
        else:
            return {
                "deployment_id": deployment_id,
                "outputs": {},
                "message": "No outputs available"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get outputs: {str(e)}")


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health & Status"],
    summary="Detailed Health Check",
    description="Comprehensive health check with Terraform and deployment statistics"
)
async def health_check():
    """
    Detailed health check with service statistics.
    """
    try:
        # Get Terraform version
        result = subprocess.run(
            ["terraform", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        tf_version = "unknown"
        if result.returncode == 0:
            # Extract version from output
            version_line = result.stdout.split('\n')[0]
            tf_version = version_line.replace("Terraform v", "")
        
        # Count active deployments
        active = sum(1 for d in deployments_db.values() 
                    if d["status"] in ["initializing", "planning", "applying", "destroying"])
        
        return HealthResponse(
            status="healthy",
            terraform_version=tf_version,
            active_deployments=active,
            total_deployments=len(deployments_db),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        return HealthResponse(
            status="degraded",
            terraform_version="error",
            active_deployments=0,
            total_deployments=len(deployments_db),
            timestamp=datetime.now().isoformat()
        )


@app.get(
    "/stats",
    tags=["Health & Status"],
    summary="Service Statistics",
    description="Get detailed statistics about deployments"
)
async def get_stats():
    """Get deployment statistics"""
    stats = {
        "total_deployments": len(deployments_db),
        "by_status": {},
        "recent_deployments": []
    }
    
    # Count by status
    for deployment in deployments_db.values():
        status = deployment["status"]
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
    
    # Recent deployments
    recent = sorted(
        deployments_db.values(),
        key=lambda x: x["created_at"],
        reverse=True
    )[:5]
    
    stats["recent_deployments"] = [
        {
            "deployment_id": d["deployment_id"],
            "deployment_name": d["deployment_name"],
            "status": d["status"],
            "created_at": d["created_at"]
        }
        for d in recent
    ]
    
    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)