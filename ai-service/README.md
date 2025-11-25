# 🧠 AI Service - Natural Language Processing & Code Generation

## Overview

The **AI Service** is the brain of the AI DevOps Assistant. It uses Claude AI to understand user requests in natural language and generate production-ready Terraform infrastructure code.

## 🎯 What This Service Does

### 1. **Intent Parsing** 
Converts natural language to structured infrastructure requirements:
```
User: "Create a VPC with 2 private subnets"
↓
Output: {
  "resources": ["vpc", "subnet"],
  "requirements": {
    "vpc_count": 1,
    "subnet_count": 2,
    "subnet_type": "private"
  },
  "estimated_complexity": "simple",
  "needs_rag": true
}
```

### 2. **Code Generation**
Creates production-ready Terraform code with best practices:
```python
# Takes: Intent + RAG context + Policies
# Produces: Complete Terraform code with:
- Proper resource naming
- Security configurations
- AWS best practices
- Comments and documentation
```

### 3. **Code Refinement**
Improves code based on validation feedback:
```
Cost too high? → Optimize resource types
Security issues? → Add encryption, tighten rules
Quota exceeded? → Suggest alternatives
```

## 🏗️ Architecture

```
┌─────────────────┐
│   User Input    │
│ "Create VPC..." │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│   Intent Parser         │
│   (Claude AI)           │
│ Extracts: resources,    │
│ requirements, complexity│
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   RAG Service           │
│   (if needs_rag=true)   │
│ Fetches best practices  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Code Generator        │
│   (Claude AI)           │
│ Creates Terraform code  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   MCP Validation        │
│ Cost, Security, Quotas  │
└─────────────────────────┘
```

## 📁 File Structure

```
ai-service/
├── main.py              # FastAPI application with endpoints
├── config.py            # Configuration and settings
├── utils.py             # Helper functions for Claude AI
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
└── .env.example        # Environment variables template
```

## 🚀 API Endpoints

### 1. POST `/parse-intent`
Parse natural language into structured infrastructure intent.

**Request:**
```json
{
  "message": "Create a 3-tier application with load balancer and database",
  "context": {
    "region": "us-east-1"
  }
}
```

**Response:**
```json
{
  "resources": ["alb", "ec2", "rds"],
  "requirements": {
    "tiers": 3,
    "load_balancer": true,
    "database": true
  },
  "estimated_complexity": "moderate",
  "needs_rag": true
}
```

### 2. POST `/generate-code`
Generate Terraform code from parsed intent.

**Request:**
```json
{
  "intent": {
    "resources": ["vpc", "subnet"],
    "requirements": {...}
  },
  "rag_context": [
    {"content": "VPC best practice: Use /16 CIDR..."}
  ],
  "organization_policies": {
    "tagging": "All resources must have Environment tag"
  }
}
```

**Response:**
```json
{
  "terraform_code": "resource \"aws_vpc\" \"main\" {...}",
  "explanation": "Creates VPC with 2 private subnets...",
  "resources_created": ["aws_vpc", "aws_subnet"],
  "estimated_cost_info": "$45/month - NAT Gateway $32, VPC free"
}
```

### 3. POST `/refine-code`
Refine code based on validation feedback.

**Request:**
```json
{
  "original_code": "resource \"aws_instance\" \"app\" {...}",
  "feedback": "Cost too high, use smaller instance type",
  "validation_results": {
    "monthly_cost": 250,
    "issues": ["t3.2xlarge too expensive"]
  }
}
```

### 4. GET `/health`
Service health check with Claude API status.

## 🔧 Setup & Installation

### Prerequisites
- Python 3.11+
- Anthropic API key

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment:**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. **Run the service:**
```bash
python main.py
# or
uvicorn main:app --reload --port 8001
```

4. **Test the service:**
```bash
curl http://localhost:8001/
```

### Docker Deployment

```bash
# Build image
docker build -t ai-service:latest .

# Run container
docker run -d \
  --name ai-service \
  -p 8001:8001 \
  -e ANTHROPIC_API_KEY=your-key \
  ai-service:latest
```

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude AI API key | Required |
| `CLAUDE_MODEL` | Model to use | `claude-sonnet-4-20250514` |
| `MAX_TOKENS` | Max response tokens | `4000` |
| `SERVICE_PORT` | Service port | `8001` |
| `RAG_SERVICE_URL` | RAG service endpoint | `http://rag-service:8002` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 🧪 Testing

Run tests:
```bash
pytest tests/ -v --cov=.
```

Test endpoints manually:
```bash
# Parse intent
curl -X POST http://localhost:8001/parse-intent \
  -H "Content-Type: application/json" \
  -d '{"message": "Create VPC with 2 subnets"}'

# Generate code
curl -X POST http://localhost:8001/generate-code \
  -H "Content-Type: application/json" \
  -d @sample_request.json
```

## 📊 How Claude AI is Used

### Intent Parsing
- **Model:** Claude Sonnet 4
- **Task:** Extract structured data from natural language
- **Input:** User's infrastructure request
- **Output:** JSON with resources, requirements, complexity

### Code Generation
- **Model:** Claude Sonnet 4
- **Task:** Generate production-ready Terraform code
- **Input:** Intent + Best practices + Policies
- **Output:** Complete Terraform configuration with explanations

### Code Refinement
- **Model:** Claude Sonnet 4
- **Task:** Improve code based on validation feedback
- **Input:** Original code + Issues found
- **Output:** Refined code with fixes applied

## 🔍 Key Features

✅ **Natural Language Understanding**: Parse complex infrastructure requests  
✅ **Context-Aware Generation**: Uses RAG results and policies  
✅ **Best Practices Built-in**: AWS Well-Architected Framework  
✅ **Security First**: Adds encryption, proper IAM, security groups  
✅ **Cost Conscious**: Provides cost estimates  
✅ **Iterative Refinement**: Improves code based on feedback  

## 🔗 Integration with Other Services

- **RAG Service**: Fetches best practices when `needs_rag=true`
- **MCP Service**: Receives validation feedback for refinement
- **Infrastructure Service**: Provides generated code for deployment

## 📈 Performance

- **Intent Parsing**: ~2-3 seconds
- **Code Generation**: ~5-8 seconds
- **Code Refinement**: ~4-6 seconds

## 🐛 Troubleshooting

**Claude API errors:**
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Test connectivity
curl -X POST http://localhost:8001/health
```

**JSON parsing errors:**
- Claude sometimes wraps responses in markdown
- The `utils.py` handles this automatically
- Check logs for raw responses if issues persist

## 📝 Example Usage Flow

```python
# 1. User sends request
request = {"message": "Create VPC with 2 subnets"}

# 2. Parse intent
intent = await parse_intent(request)
# Output: {resources: ["vpc", "subnet"], ...}

# 3. If needs RAG, fetch best practices
if intent.needs_rag:
    context = await rag_service.search(intent.resources)

# 4. Generate code
code = await generate_code(intent, context)
# Output: Complete Terraform code

# 5. Validate with MCP
validation = await mcp_service.validate(code)

# 6. If issues found, refine
if validation.has_issues:
    refined = await refine_code(code, validation.feedback)
```

## 🎓 Learning Resources

- [Claude AI Documentation](https://docs.anthropic.com/)
- [AWS Terraform Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Service Status:** ✅ Production Ready  
**Port:** 8001  
**Dependencies:** Claude AI API, RAG Service