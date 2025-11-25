# 🚀 Infrastructure Service - Terraform Deployment & Management

## Overview

The **Infrastructure Service** is the deployment engine that executes Terraform code to create AWS infrastructure. It manages the complete Terraform lifecycle: init, plan, apply, and destroy.

## 🎯 What This Service Does

### 1. **Terraform Initialization**
Set up working directory and download providers:
```bash
terraform init
```

### 2. **Plan Generation**
Preview what will be created:
```bash
terraform plan
# Output: 5 to add, 0 to change, 0 to destroy
```

### 3. **Infrastructure Deployment**
Create AWS resources:
```bash
terraform apply
# Creates: VPC, Subnets, NAT Gateway, etc.
```

### 4. **Resource Destruction**
Clean up infrastructure:
```bash
terraform destroy
```

### 5. **State Management**
Track deployed resources and their state.

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  INFRASTRUCTURE SERVICE (Port 8004)     │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Deployment Manager             │   │
│  │  • Create workspace             │   │
│  │  • Track deployment status      │   │
│  │  • Manage lifecycle             │   │
│  └─────────────────────────────────┘   │
│                   ↓                     │
│  ┌─────────────────────────────────┐   │
│  │  Terraform Executor             │   │
│  │  • terraform init               │   │
│  │  • terraform plan               │   │
│  │  • terraform apply              │   │
│  │  • terraform destroy            │   │
│  └─────────────────────────────────┘   │
│                   ↓                     │
│  ┌─────────────────────────────────┐   │
│  │  State Manager                  │   │
│  │  • Local state storage          │   │
│  │  • S3 backend (optional)        │   │
│  │  • State locking                │   │
│  └─────────────────────────────────┘   │
│                   ↓                     │
│             AWS Resources               │
│      (VPC, EC2, RDS, S3, etc.)         │
│                                         │
└─────────────────────────────────────────┘
```

## 📁 File Structure

```
infra-service/
├── main.py              # FastAPI application
├── config.py            # Configuration
├── start.py             # Startup script
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container with Terraform
├── docker-compose.yml  # Easy deployment
├── .env.example        # Environment template
└── README.md           # Documentation
```

## 🚀 API Endpoints

### Deployments

#### POST `/deployments`
Create a new deployment.

**Request:**
```json
{
  "terraform_code": "resource \"aws_vpc\" \"main\" { cidr_block = \"10.0.0.0/16\" }",
  "deployment_name": "production-vpc",
  "region": "us-east-1",
  "auto_approve": false,
  "tags": {
    "Environment": "production"
  }
}
```

**Response:**
```json
{
  "deployment_id": "a1b2c3d4e5f6",
  "status": "pending",
  "message": "Deployment created successfully",
  "workspace_path": "/app/workspaces/a1b2c3d4e5f6",
  "created_at": "2025-11-25T10:00:00"
}
```

#### GET `/deployments/{deployment_id}`
Get deployment status.

#### GET `/deployments`
List all deployments.

#### DELETE `/deployments/{deployment_id}`
Delete deployment record.

### Terraform Operations

#### POST `/deployments/{deployment_id}/init`
Initialize Terraform workspace.

#### POST `/deployments/{deployment_id}/plan`
Generate execution plan.

**Response:**
```json
{
  "deployment_id": "a1b2c3d4e5f6",
  "plan_output": "Terraform will perform the following actions...",
  "resources_to_add": 5,
  "resources_to_change": 0,
  "resources_to_destroy": 0,
  "plan_file_path": "/app/workspaces/a1b2c3d4e5f6/tfplan"
}
```

#### POST `/deployments/{deployment_id}/apply`
Apply Terraform changes (create infrastructure).

**Query Params:**
- `auto_approve=true` - Skip confirmation

**Response:**
```json
{
  "deployment_id": "a1b2c3d4e5f6",
  "status": "completed",
  "message": "Infrastructure deployed successfully",
  "resources_created": [
    "aws_vpc.main",
    "aws_subnet.public",
    "aws_subnet.private"
  ],
  "output": "Apply complete! Resources: 3 added, 0 changed, 0 destroyed."
}
```

#### POST `/deployments/{deployment_id}/destroy`
Destroy infrastructure.

**Query Params:**
- `auto_approve=true` - Required for destroy

#### GET `/deployments/{deployment_id}/output`
Get Terraform output values.

### Health

#### GET `/health`
Service health check.

#### GET `/stats`
Deployment statistics.

## 🔧 Setup & Installation

### Prerequisites
- Docker (recommended)
- AWS credentials (for actual deployments)
- Terraform (included in Docker image)

### Quick Start

**Option 1: Docker Compose (Recommended)**
```bash
cd infra-service

# Set AWS credentials
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Or create .env file
cat > .env << EOF
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
EOF

# Start service
docker-compose up -d

# Check health
curl http://localhost:8004/health
```

**Option 2: Local Development**
```bash
# Install Terraform first
# https://www.terraform.io/downloads

# Install Python dependencies
pip install -r requirements.txt

# Set environment
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Run service
python start.py
```

## 📊 Complete Deployment Flow

### 1. Create Deployment
```bash
curl -X POST http://localhost:8004/deployments \
  -H "Content-Type: application/json" \
  -d '{
    "terraform_code": "resource \"aws_vpc\" \"main\" { cidr_block = \"10.0.0.0/16\" }",
    "deployment_name": "my-vpc",
    "region": "us-east-1"
  }'

# Response: { "deployment_id": "abc123", "status": "pending" }
```

### 2. Initialize Terraform
```bash
curl -X POST http://localhost:8004/deployments/abc123/init

# Response: { "status": "initialized", "message": "Terraform initialized successfully" }
```

### 3. Generate Plan
```bash
curl -X POST http://localhost:8004/deployments/abc123/plan

# Response: {
#   "resources_to_add": 1,
#   "resources_to_change": 0,
#   "resources_to_destroy": 0
# }
```

### 4. Apply Changes
```bash
curl -X POST "http://localhost:8004/deployments/abc123/apply?auto_approve=true"

# Response: {
#   "status": "completed",
#   "resources_created": ["aws_vpc.main"]
# }
```

### 5. Check Status
```bash
curl http://localhost:8004/deployments/abc123

# Response: {
#   "deployment_id": "abc123",
#   "status": "completed",
#   "progress_percentage": 100,
#   "resources_created": ["aws_vpc.main"]
# }
```

### 6. Get Outputs (if defined)
```bash
curl http://localhost:8004/deployments/abc123/output

# Response: {
#   "outputs": {
#     "vpc_id": {"value": "vpc-12345"}
#   }
# }
```

### 7. Destroy (when done)
```bash
curl -X POST "http://localhost:8004/deployments/abc123/destroy?auto_approve=true"

# Response: { "status": "destroyed" }
```

## 🔄 Deployment States

```
pending → initializing → initialized → planning → planned → applying → completed
                                                               ↓
                                                            failed
                           
completed → destroying → destroyed
```

## 🔑 AWS Credentials

### Method 1: Environment Variables (Recommended)
```bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_REGION=us-east-1
```

### Method 2: .env File
```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
```

### Method 3: IAM Role (for EC2/ECS)
Service will automatically use IAM role if running on AWS.

## 💾 State Management

### Local Backend (Default)
State stored in workspace directory:
```
/app/workspaces/{deployment_id}/terraform.tfstate
```

### S3 Backend (Production)
Configure in `.env`:
```bash
STATE_BACKEND=s3
S3_STATE_BUCKET=my-terraform-state
S3_STATE_KEY_PREFIX=terraform-state
DYNAMODB_LOCK_TABLE=terraform-locks
```

## 🔗 Integration with Other Services

### Complete Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ AI Service  │ →   │ MCP Service │ →   │ Infra Svc   │ →   │     AWS     │
│  Generate   │     │  Validate   │     │   Deploy    │     │  Resources  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Example Integration
```python
# 1. AI generates code
terraform_code = ai_service.generate_code(user_request)

# 2. MCP validates
validation = mcp_service.validate(terraform_code)

if validation["deployment_ready"]:
    # 3. Deploy via Infrastructure Service
    deployment = infra_service.create_deployment({
        "terraform_code": terraform_code,
        "deployment_name": "production-app",
        "auto_approve": True
    })
    
    # 4. Initialize and apply
    infra_service.init(deployment["deployment_id"])
    infra_service.plan(deployment["deployment_id"])
    result = infra_service.apply(deployment["deployment_id"])
    
    print(f"Deployed: {result['resources_created']}")
```

## 📈 Performance

| Operation | Avg Time |
|-----------|----------|
| Create Deployment | < 1s |
| Terraform Init | 10-30s |
| Terraform Plan | 5-20s |
| Terraform Apply | 1-10min (depends on resources) |
| Terraform Destroy | 1-5min |

## 🐛 Troubleshooting

### Terraform Not Found
```bash
# Check Terraform installation
docker exec infra-service terraform version

# Should output: Terraform v1.6.6
```

### AWS Credentials Invalid
```bash
# Check environment variables
docker exec infra-service env | grep AWS

# Test AWS access
docker exec infra-service aws sts get-caller-identity
```

### Deployment Stuck
```bash
# Check deployment status
curl http://localhost:8004/deployments/{id}

# View logs
docker logs infra-service

# Check workspace
docker exec infra-service ls -la /app/workspaces/{deployment_id}
```

### State Lock Issues
```bash
# If state is locked, wait for operation to complete
# Or manually unlock (dangerous!)
docker exec -it infra-service bash
cd /app/workspaces/{deployment_id}
terraform force-unlock {lock_id}
```

## 🔒 Security Best Practices

### 1. **Protect AWS Credentials**
- Never commit credentials to version control
- Use IAM roles when possible
- Rotate credentials regularly
- Use least-privilege permissions

### 2. **Secure State Files**
- Use S3 backend with encryption
- Enable versioning on state bucket
- Use DynamoDB for state locking
- Restrict S3 bucket access

### 3. **Audit Deployments**
- Log all Terraform operations
- Track who deployed what
- Review plans before applying
- Use approval workflows

### 4. **Network Security**
- Run service in private network
- Use VPN or bastion for access
- Restrict API access with auth
- Monitor for unauthorized deployments

## 💡 Best Practices

### 1. **Always Review Plans**
```bash
# Generate plan first
POST /deployments/{id}/plan

# Review output
# Then apply if looks good
POST /deployments/{id}/apply?auto_approve=true
```

### 2. **Use Meaningful Names**
```json
{
  "deployment_name": "production-vpc-us-east-1",
  "tags": {
    "Environment": "production",
    "Owner": "platform-team",
    "CostCenter": "engineering"
  }
}
```

### 3. **Track Deployments**
```bash
# List all deployments
GET /deployments

# Filter by status
GET /deployments?status=completed
```

### 4. **Clean Up Old Deployments**
```bash
# Destroy resources first
POST /deployments/{id}/destroy?auto_approve=true

# Then delete record
DELETE /deployments/{id}?delete_workspace=true
```

## 🎯 Future Enhancements

Planned features:
- Terraform Cloud backend support
- Multi-environment management
- Deployment rollback capabilities
- Drift detection
- Cost estimation integration
- Approval workflows
- Webhook notifications
- Deployment scheduling

## 📚 Swagger Documentation

Access interactive API docs:
- Swagger UI: http://localhost:8004/docs
- ReDoc: http://localhost:8004/redoc

## 🔗 Related Services

- **AI Service** (Port 8001): Generates Terraform code
- **RAG Service** (Port 8002): Provides best practices
- **MCP Service** (Port 8003): Validates before deployment

---

**Service Status:** ✅ Production Ready  
**Port:** 8004  
**Dependencies:** Terraform, AWS Credentials  
**Integration:** Final step in deployment pipeline
