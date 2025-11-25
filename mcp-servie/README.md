# ⚡ MCP Service - Validation & Analysis

## Overview

The **MCP Service** (Model Context Protocol / Validation Service) validates Terraform infrastructure code before deployment. It checks costs, security, quotas, and dependencies to ensure safe and cost-effective deployments.

## 🎯 What This Service Does

### 1. **Cost Estimation**
Calculate monthly AWS costs before deployment:
```
EC2 t3.large + 100GB EBS = $60.74 + $8.00 = $68.74/month
```

### 2. **Security Validation**
Check against security best practices:
- ✅ Encryption at rest enabled
- ✅ No public access (0.0.0.0/0)
- ✅ IAM least privilege
- ✅ RDS not publicly accessible

### 3. **Quota Checking**
Verify AWS service limits:
```
Requested: 5 EC2 instances
Limit: 20 instances
Status: ✅ OK (25% of limit)
```

### 4. **Resource Validation**
Analyze Terraform dependencies and best practices.

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│       MCP SERVICE (Port 8003)           │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Cost Analyzer                  │   │
│  │  • AWS Pricing Database         │   │
│  │  • Per-resource calculation     │   │
│  │  • Monthly cost estimation      │   │
│  └─────────────────────────────────┘   │
│                   ↓                     │
│  ┌─────────────────────────────────┐   │
│  │  Security Validator             │   │
│  │  • Encryption checks            │   │
│  │  • Access control rules         │   │
│  │  • IAM policy analysis          │   │
│  └─────────────────────────────────┘   │
│                   ↓                     │
│  ┌─────────────────────────────────┐   │
│  │  Quota Checker                  │   │
│  │  • AWS service limits           │   │
│  │  • Resource counting            │   │
│  │  • Warning thresholds           │   │
│  └─────────────────────────────────┘   │
│                   ↓                     │
│  ┌─────────────────────────────────┐   │
│  │  Validation Report              │   │
│  │  • Deployment readiness         │   │
│  │  • Recommendations              │   │
│  │  • Risk assessment              │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

## 📁 File Structure

```
mcp-service/
├── main.py              # FastAPI application with endpoints
├── config.py            # Configuration and pricing data
├── start.py             # Startup script
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Easy deployment
├── .env.example        # Environment variables template
└── README.md           # Documentation
```

## 🚀 API Endpoints

### Validation

#### POST `/validate`
Complete validation of Terraform code.

**Request:**
```json
{
  "terraform_code": "resource \"aws_instance\" \"web\" { ... }",
  "region": "us-east-1",
  "validation_level": "standard"
}
```

**Response:**
```json
{
  "validation_id": "a1b2c3d4e5f6",
  "status": "passed",
  "total_monthly_cost": 68.74,
  "security_score": 90,
  "security_issues": [],
  "quota_warnings": [],
  "deployment_ready": true,
  "recommendations": [
    "Consider using Reserved Instances for cost savings"
  ]
}
```

### Cost Analysis

#### POST `/cost-analysis`
Cost estimation only.

#### GET `/pricing/{resource_type}`
Get pricing for specific AWS resource.

### Security

#### POST `/security-check`
Security validation only.

### Quotas

#### POST `/quota-check`
Check AWS service quotas.

#### GET `/quotas/{service}`
Get quota limits for AWS service.

### Health

#### GET `/health`
Service health check.

#### GET `/stats`
Service statistics.

## 🔧 Setup & Installation

### Quick Start

**Docker Compose (Recommended)**
```bash
cd mcp-service

# Start service
docker-compose up -d

# Test validation
curl -X POST http://localhost:8003/validate \
  -H "Content-Type: application/json" \
  -d @sample_request.json
```

**Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python start.py

# Test
curl http://localhost:8003/health
```

**Docker**
```bash
docker build -t mcp-service .
docker run -p 8003:8003 mcp-service
```

## 📊 Cost Estimation

### Supported Resources

| Resource | Pricing Model |
|----------|---------------|
| **EC2** | Hourly rate + EBS storage |
| **RDS** | Instance + storage + Multi-AZ |
| **NAT Gateway** | Hourly + data transfer |
| **ALB/NLB** | Hourly + LCU charges |
| **S3** | Per GB storage |
| **EBS** | Per GB by volume type |

### Example Costs (us-east-1)

```
t3.micro:   $7.59/month
t3.small:   $15.18/month
t3.medium:  $30.37/month
t3.large:   $60.74/month
t3.xlarge:  $121.49/month

RDS db.t3.micro:  $12.41/month
RDS db.t3.small:  $24.82/month

NAT Gateway: $32.85/month + data
ALB:         $16.43/month + LCU
```

## 🔒 Security Rules

### Built-in Security Checks

#### SEC001: Encryption at Rest
- **Severity:** High
- **Check:** EBS, RDS, S3 have encryption enabled
- **Fix:** Add `encrypted = true`

#### SEC002: Public Access Prevention
- **Severity:** Critical
- **Check:** No 0.0.0.0/0 in security groups
- **Fix:** Restrict to specific IP ranges

#### SEC003: S3 Bucket Security
- **Severity:** Critical
- **Check:** No public-read ACLs
- **Fix:** Use private ACL

#### SEC004: IAM Least Privilege
- **Severity:** Medium
- **Check:** No wildcard (*) permissions
- **Fix:** Specify exact permissions

#### SEC005: RDS Public Access
- **Severity:** High
- **Check:** RDS not publicly accessible
- **Fix:** Set `publicly_accessible = false`

## 📈 AWS Quotas

### Default Limits (Checked)

```
EC2:
  - Instances: 20
  - vCPUs: 64
  - Elastic IPs: 5

VPC:
  - VPCs per region: 5
  - Subnets per VPC: 200
  - Security Groups: 2,500
  - NAT Gateways: 5

RDS:
  - Instances: 40
  - Storage: 100TB

S3:
  - Buckets: 100
```

## 🧪 Testing

### Test Complete Validation
```bash
curl -X POST http://localhost:8003/validate \
  -H "Content-Type: application/json" \
  -d '{
    "terraform_code": "resource \"aws_instance\" \"web\" {\n  ami = \"ami-123\"\n  instance_type = \"t3.micro\"\n}",
    "region": "us-east-1"
  }'
```

### Test Cost Analysis
```bash
curl -X POST http://localhost:8003/cost-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "terraform_code": "resource \"aws_instance\" \"web\" { instance_type = \"t3.large\" }",
    "region": "us-east-1"
  }'
```

### Test Security Check
```bash
curl -X POST http://localhost:8003/security-check \
  -H "Content-Type: application/json" \
  -d '{
    "terraform_code": "resource \"aws_security_group\" \"allow_all\" { ingress { cidr_blocks = [\"0.0.0.0/0\"] } }"
  }'
```

### Get Pricing Info
```bash
curl http://localhost:8003/pricing/ec2
```

### Get Quota Limits
```bash
curl http://localhost:8003/quotas/ec2
```

## 🔄 Integration with Other Services

### With AI Service
```
AI Service generates code
    ↓
MCP Service validates
    ↓
If issues found → AI Service refines
    ↓
If passed → Infrastructure Service deploys
```

### Example Integration
```python
# AI Service calls MCP for validation
validation_result = requests.post(
    "http://mcp-service:8003/validate",
    json={"terraform_code": generated_code}
)

if validation_result["deployment_ready"]:
    # Safe to deploy
    deploy(generated_code)
else:
    # Refine code based on issues
    refined_code = refine(
        original_code,
        validation_result["security_issues"],
        validation_result["recommendations"]
    )
```

## 📊 Validation Levels

### Basic
- Cost estimation only
- No security checks
- Fast validation

### Standard (Default)
- Cost estimation
- Security validation
- Quota checking
- Basic dependency analysis

### Strict
- All standard checks
- Enforce encryption
- No public access allowed
- Strict naming conventions
- Required tags validation

## 💡 Best Practices

### 1. **Always Validate Before Deploy**
```bash
# Bad: Deploy directly
terraform apply

# Good: Validate first
curl -X POST http://mcp:8003/validate ... && terraform apply
```

### 2. **Set Cost Thresholds**
```bash
# In .env
MAX_COST_THRESHOLD=500.0
```

### 3. **Use Strict Validation for Production**
```json
{
  "validation_level": "strict"
}
```

### 4. **Review Security Issues**
Always fix critical and high severity issues before deployment.

## 📈 Performance

| Endpoint | Avg Time |
|----------|----------|
| `/validate` | 100-300ms |
| `/cost-analysis` | 50-100ms |
| `/security-check` | 50-150ms |
| `/quota-check` | 10-50ms |

## 🐛 Troubleshooting

### Validation Fails
```bash
# Check logs
docker logs mcp-service

# Verify Terraform syntax
terraform validate
```

### Cost Estimation Inaccurate
```bash
# Check pricing data in config.py
# Update with latest AWS pricing
```

### Security False Positives
```bash
# Adjust validation level
validation_level: "basic"
```

## 🎯 Future Enhancements

Planned features:
- Real-time AWS pricing API integration
- Actual AWS quota checking via API
- Custom security rule definitions
- Multi-region cost comparison
- Terraform plan file analysis
- Cost trend analysis

## 📚 Swagger Documentation

Access interactive API docs:
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

## 🔗 Related Services

- **AI Service** (Port 8001): Generates Terraform code
- **RAG Service** (Port 8002): Provides best practices
- **Infrastructure Service** (Port 8004): Deploys validated code

---

**Service Status:** ✅ Production Ready  
**Port:** 8003  
**No External Dependencies:** Works standalone  
**Integration:** AI Service, Infrastructure Service
